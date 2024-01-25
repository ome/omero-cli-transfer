# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2022 The Jackson Laboratory
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

"""
   Plugin for transfering objects and annotations between servers

"""

from pathlib import Path
import sys
import os
import copy
from functools import wraps
import shutil
from typing import DefaultDict
import hashlib
from zipfile import ZipFile
from typing import Callable, List, Any, Dict, Union, Optional, Tuple
import xml.etree.cElementTree as ETree

from generate_xml import populate_xml, populate_tsv, populate_rocrate
from generate_xml import populate_xml_folder
from generate_omero_objects import populate_omero, get_server_path

import ezomero
from ome_types.model import XMLAnnotation, OME
from ome_types import from_xml, to_xml
from omero.sys import Parameters
from omero.rtypes import rstring
from omero.cli import CLI, GraphControl
from omero.cli import ProxyStringType
from omero.gateway import BlitzGateway
from omero.model import Image, Dataset, Project, Plate, Screen
from omero.grid import ManagedRepositoryPrx as MRepo

DIR_PERM = 0o755
MD5_BUF_SIZE = 65536


HELP = ("""Transfer objects and annotations between servers.

Both subcommands (pack and unpack) will use an existing OMERO session
created via CLI or prompt the user for parameters to create one.
""")

PACK_HELP = ("""Creates transfer packet for moving objects.

This subcommand creates a transfer packet for moving objects between
OMERO server instances.

The syntax for specifying objects is: <object>:<id>
<object> can be Image, Project or Dataset.
Project is assumed if <object>: is omitted.
A file path needs to be provided; a tar file with the contents of
the packet will be created at the specified path.

Currently, only MapAnnotations, Tags, FileAnnotations and CommentAnnotations
are packaged into the transfer pack, and only Point, Line, Ellipse, Rectangle
and Polygon-type ROIs are packaged.

--zip packs the object into a compressed zip file rather than a tarball.

--figure includes OMERO.Figures; note that this can lead to a performance
hit and that Figures can reference images that are not included in your pack!

--barchive creates a package compliant with Bioimage Archive submission
standards - see repo README for more detail. This package format is not
compatible with unpack usage.

--rocrate generates a RO-Crate compliant package with flat structure (all image
files in a single folder). A JSON metadata file is added with basic information
about the files (name, mimetype).

--simple creates a package that is "human readable" - folders will be created
for projects/datasets, with files being placed according to where they come
from in the server. Note this a package generated with this option is NOT
guaranteed to work with unpack.

--metadata allows you to specify which transfer metadata will be saved in
`transfer.xml` as possible MapAnnotation values to the images. Default is `all`
(equivalent to `img_id timestamp software version hostname md5 orig_user
orig_group`), other options are `none`, `img_id`, `timestamp`, `software`,
`version`, `md5`, `hostname`, `db_id`, `orig_user`, `orig_group`.

--binaries allows to specify whether to archive binary data
(e.g images, ROIs, FileAnnotations) or only create the transfer.xml.
Default is `all` and will create the archive.
With `none`, only the `transfer.xml` file is created, in which case
the last cli argument is the path where the `transfer.xml` file
will be written.

Examples:
omero transfer pack Image:123 transfer_pack.tar
omero transfer pack --zip Image:123 transfer_pack.zip
omero transfer pack Dataset:1111 /home/user/new_folder/new_pack.tar
omero transfer pack 999 tarfile.tar  # equivalent to Project:999
omero transfer pack 1 transfer_pack.tar --metadata img_id version db_id
omero transfer pack --binaries none Dataset:1111 /home/user/new_folder/
omero transfer pack --binaries all Dataset:1111 /home/user/new_folder/pack.tar
""")

UNPACK_HELP = ("""Unpacks a transfer packet into an OMERO hierarchy.

Unpacks an existing transfer packet, imports images
as orphans and uses the XML contained in the transfer packet to re-create
links, annotations and ROIs.

--ln_s forces imports to use the transfer=ln_s option, in-place importing
files. Same restrictions of regular in-place imports apply.

--output allows for specifying an optional output folder where the packet
will be unzipped.

--folder allows the user to point to a previously-unpacked folder rather than
a single file.

--merge will use existing Projects, Datasets and Screens if the current user
already owns entities with the same name as ones defined in `transfer.xml`,
effectively merging the "new" unpacked entities with existing ones.

--figure unpacks and updates Figures, if your pack contains those. Note that
there's no guaranteed behavior for images referenced on Figures that were not
included in a pack. You can just have an image missing, a completely unrelated
image, a permission error. Use at your own risk!

--metadata allows you to specify which transfer metadata will be used from
`transfer.xml` as MapAnnotation values to the images. Fields that do not
exist on `transfer.xml` will be ignored. Default is `all` (equivalent to
`img_id timestamp software version hostname md5 orig_user orig_group`), other
options are `none`, `img_id`, `timestamp`, `software`, `version`, `md5`,
`hostname`, `db_id`, `orig_user`, `orig_group`.

You can also pass all --skip options that are allowed by `omero import` (all,
checksum, thumbnails, minmax, upgrade).

Examples:
omero transfer unpack transfer_pack.zip
omero transfer unpack --output /home/user/optional_folder --ln_s
omero transfer unpack --folder /home/user/unpacked_folder/ --skip upgrade
omero transfer unpack pack.tar --metadata db_id orig_user hostname
""")

PREPARE_HELP = ("""Creates an XML from a folder with images.

Creates an XML file appropriate for usage with `omero transfer unpack` from
a folder that contains image files, rather than a source OMERO server. This
is intended as a first step on a bulk-import workflow, followed by using
`omero transfer unpack` to complete an import.

Note: images imported from an XML generated with this tool will have whichever
names `showinf` reports them to have; that is, the names on their internal
metadata, which might be different from filenames. For multi-image files,
image names follow the pattern "filename [imagename]", where 'imagename' is
the one reported by `showinf`.

--filelist allows you to specify a text file containing a list of file paths
(one per line). Relative paths should be relative to the location of the file
list. The XML file will only take those files into consideration.
The resulting `transfer.xml` file will be created on the same directory of
your file list.

Examples:
omero transfer prepare /home/user/folder_with_files
omero transfer prepare --filelist /home/user/file_with_paths.txt
""")


def gateway_required(func: Callable) -> Callable:
    """
    Decorator which initializes a client (self.client),
    a BlitzGateway (self.gateway), and makes sure that
    all services of the Blitzgateway are closed again.
    """
    @wraps(func)
    def _wrapper(self, *args, **kwargs):
        self.client = self.ctx.conn(*args)
        self.session = self.client.getSessionId()
        self.gateway = BlitzGateway(client_obj=self.client)
        router = self.client.getRouter(self.client.getCommunicator())
        self.hostname = str(router).split('-h ')[-1].split()[0]
        try:
            return func(self, *args, **kwargs)
        finally:
            if self.gateway is not None:
                self.gateway.close(hard=False)
                self.gateway = None
                self.client = None
    return _wrapper


class TransferControl(GraphControl):

    def _configure(self, parser):
        parser.add_login_arguments()
        sub = parser.sub()
        pack = parser.add(sub, self.pack, PACK_HELP)
        unpack = parser.add(sub, self.unpack, UNPACK_HELP)
        prepare = parser.add(sub, self.prepare, PREPARE_HELP)

        render_type = ProxyStringType("Project")
        obj_help = ("Object to be packed for transfer")
        pack.add_argument("object", type=render_type, help=obj_help)
        file_help = ("Path to where the packed file will be saved")
        pack.add_argument(
                "--zip", help="Pack into a zip file rather than a tarball",
                action="store_true")
        pack.add_argument(
                "--figure", help="Include OMERO.Figures into the pack"
                                 " (caveats apply)",
                action="store_true")
        pack.add_argument(
                "--barchive", help="Pack into a file compliant with Bioimage"
                                   " Archive submission standards",
                action="store_true")
        pack.add_argument(
                "--rocrate", help="Pack into a file compliant with "
                                  "RO-Crate standards",
                action="store_true")
        pack.add_argument(
                "--simple", help="Pack into a human-readable package file",
                action="store_true")
        pack.add_argument(
            "--metadata",
            choices=['all', 'none', 'img_id', 'timestamp',
                     'software', 'version', 'md5', 'hostname', 'db_id',
                     'orig_user', 'orig_group'], nargs='+',
            help="Metadata field to be added to MapAnnotation"
        )
        pack.add_argument(
                "--plugin", help="Use external plugin for packing.",
                type=str)
        pack.add_argument("filepath", type=str, help=file_help)
        pack.add_argument(
            "--binaries",
            choices=["all", "none"],
            default="all",
            help="With `--binaries none`, only generate the metadata file "
                 "(transfer.xml or ro-crate-metadata.json). "
                 "With `--binaries all` (the default), both pixel data "
                 "and annotation are saved.")

        file_help = ("Path to where the zip file is saved")
        unpack.add_argument("filepath", type=str, help=file_help)
        unpack.add_argument(
                "--ln_s_import", help="Use in-place import",
                action="store_true")
        unpack.add_argument(
                "--merge", help="Use existing entities if possible",
                action="store_true")
        unpack.add_argument(
                "--figure", help="Use OMERO.Figures if present"
                                 " (caveats apply)",
                action="store_true")
        unpack.add_argument(
                "--folder", help="Pass path to a folder rather than a pack",
                action="store_true")
        unpack.add_argument(
            "--output", type=str, help="Output directory where zip "
                                       "file will be extracted"
        )
        unpack.add_argument(
            "--skip", choices=['all', 'checksum', 'thumbnails', 'minmax',
                               'upgrade'],
            help="Skip options to be passed to omero import"
        )
        unpack.add_argument(
            "--metadata",
            choices=['all', 'none', 'img_id', 'plate_id', 'timestamp',
                     'software', 'version', 'md5', 'hostname', 'db_id',
                     'orig_user', 'orig_group'], nargs='+',
            help="Metadata field to be added to MapAnnotation"
        )
        folder_help = ("Path to folder with image files")
        prepare.add_argument("folder", type=str, help=folder_help)
        prepare.add_argument(
            "--filelist", help="Pass path to a filelist rather than a folder",
            action="store_true")

    @gateway_required
    def pack(self, args):
        """ Implements the 'pack' command """
        self.__pack(args)

    @gateway_required
    def unpack(self, args):
        """ Implements the 'unpack' command """
        self.__unpack(args)

    @gateway_required
    def prepare(self, args):
        """ Implements the 'prepare' command """
        self.__prepare(args)

    def _get_path_to_repo(self) -> List[str]:
        shared = self.client.sf.sharedResources()
        repos = shared.repositories()
        repos = list(zip(repos.descriptions, repos.proxies))
        mrepos = []
        for _, pair in enumerate(repos):
            desc, prx = pair
            path = "".join([desc.path.val, desc.name.val])
            is_mrepo = MRepo.checkedCast(prx)
            if is_mrepo:
                mrepos.append(path)
        return mrepos

    def _copy_files(self, id_list: Dict[str, Any], folder: str,
                    conn: BlitzGateway):
        if not isinstance(id_list, dict):
            raise TypeError("id_list must be a dict")
        if not all(isinstance(item, str) for item in id_list.keys()):
            raise TypeError("id_list keys must be strings")
        if not isinstance(folder, str):
            raise TypeError("folder must be a string")
        if not isinstance(conn, BlitzGateway):
            raise TypeError("invalid type for connection object")
        cli = CLI()
        cli.loadplugins()
        downloaded_ids = []
        for id in id_list:
            clean_id = int(id.split(":")[-1])
            dtype = id.split(":")[0]
            if (dtype == "Image"):
                if (clean_id not in downloaded_ids):
                    path = id_list[id]
                    rel_path = path
                    rel_path = str(Path(rel_path).parent)
                    subfolder = os.path.join(str(Path(folder)), rel_path)
                    os.makedirs(subfolder, mode=DIR_PERM, exist_ok=True)
                    obj = conn.getObject("Image", clean_id)
                    fileset = obj.getFileset()
                    if rel_path == "pixel_images" or fileset is None:
                        filepath = str(Path(subfolder) /
                                       (str(clean_id) + ".tiff"))
                        cli.invoke(['export', '--file', filepath, id])
                        downloaded_ids.append(id)
                    else:
                        cli.invoke(['download', id, subfolder])
                        for fs_image in fileset.copyImages():
                            downloaded_ids.append(fs_image.getId())
            else:
                path = id_list[id]
                rel_path = path
                subfolder = os.path.join(str(Path(folder)), rel_path)
                ann_folder = str(Path(subfolder).parent)
                os.makedirs(ann_folder, mode=DIR_PERM, exist_ok=True)
                id = "File" + id
                cli.invoke(['download', id, subfolder])

    def _package_files(self, tar_path: str, zip: bool, folder: str):
        if zip:
            print("Creating zip file...")
            shutil.make_archive(tar_path, 'zip', folder)
        else:
            print("Creating tar file...")
            shutil.make_archive(tar_path, 'tar', folder)

    def _process_metadata(self, metadata: Union[List[str], None]):
        if not metadata:
            metadata = ['all']
        if "all" in metadata:
            metadata.remove("all")
            metadata.extend(["img_id", "plate_id", "timestamp", "software",
                             "version", "hostname", "md5", "orig_user",
                             "orig_group"])
        if "none" in metadata:
            metadata = None
        if metadata:
            metadata = list(set(metadata))
        self.metadata = metadata

    def _fix_pixels_image_simple(self, ome: OME, folder: str, filepath: str
                                 ) -> OME:
        newome = copy.deepcopy(ome)
        for ann in ome.structured_annotations:
            if isinstance(ann.value, str) and\
               ann.value.startswith("pixel_images"):
                for img in newome.images:
                    for ref in img.annotation_refs:
                        if ref.id == ann.id:
                            this_img = img
                            path1 = ann.value
                            img.annotation_refs.remove(ref)
                            newome.structured_annotations.remove(ann)
                for ref in this_img.annotation_refs:
                    for ann in newome.structured_annotations:
                        if ref.id == ann.id:
                            if isinstance(ann.value, str):
                                path2 = ann.value
                rel_path = str(Path(path2).parent)
                subfolder = os.path.join(str(Path(folder)), rel_path)
                os.makedirs(subfolder, mode=DIR_PERM, exist_ok=True)
                shutil.move(os.path.join(str(Path(folder)), path1),
                            os.path.join(str(Path(folder)), path2))
        if os.path.exists(os.path.join(str(Path(folder)), "pixel_images")):
            shutil.rmtree(os.path.join(str(Path(folder)), "pixel_images"))
        with open(filepath, 'w') as fp:
            print(to_xml(newome), file=fp)
            fp.close()
        return newome

    def __pack(self, args):
        if isinstance(args.object, Image) or isinstance(args.object, Plate) \
           or isinstance(args.object, Screen):
            if args.barchive:
                raise ValueError("Single image, plate or screen cannot be "
                                 "packaged for Bioimage Archive")
        if isinstance(args.object, Plate) or isinstance(args.object, Screen):
            if args.rocrate:
                raise ValueError("Single image, plate or screen cannot be "
                                 "packaged in a RO-Crate")
            if args.simple:
                raise ValueError("Single plate or screen cannot be "
                                 "packaged in human-readable format")

        if (args.binaries == "none") and args.simple:
            raise ValueError("The `--binaries none` and `--simple` options "
                             "are  incompatible")

        if isinstance(args.object, Image):
            src_datatype, src_dataid = "Image", args.object.id
        elif isinstance(args.object, Dataset):
            src_datatype, src_dataid = "Dataset", args.object.id
        elif isinstance(args.object, Project):
            src_datatype, src_dataid = "Project", args.object.id
        elif isinstance(args.object, Plate):
            src_datatype, src_dataid = "Plate", args.object.id
        elif isinstance(args.object, Screen):
            src_datatype, src_dataid = "Screen", args.object.id
        else:
            print("Object is not a project, dataset, screen, plate or image")
            return
        export_types = (args.rocrate, args.barchive, args.simple)
        if sum(1 for ct in export_types if ct) > 1:
            raise ValueError("Only one special export type (RO-Crate, Bioimage"
                             " Archive, human-readable) can be specified at "
                             "once")
        self.metadata = []
        self._process_metadata(args.metadata)
        obj = self.gateway.getObject(src_datatype, src_dataid)
        if obj is None:
            raise ValueError("Object not found or outside current"
                             " permissions for current user.")
        print("Populating xml...")
        tar_path = Path(args.filepath)
        if args.binaries == "all":
            folder = str(tar_path) + "_folder"
        else:
            folder = os.path.splitext(tar_path)[0]
            print(f"Output will be written to {folder}")

        os.makedirs(folder, mode=DIR_PERM, exist_ok=True)
        if args.barchive:
            md_fp = str(Path(folder) / "submission.tsv")
        elif args.rocrate:
            md_fp = str(Path(folder) / "ro-crate-metadata.json")
        else:
            md_fp = str(Path(folder) / "transfer.xml")
            print(f"Saving metadata at {md_fp}.")
        ome, path_id_dict = populate_xml(src_datatype, src_dataid, md_fp,
                                         self.gateway, self.hostname,
                                         args.barchive, args.simple,
                                         args.figure,
                                         self.metadata)

        if args.binaries == "all":
            print("Starting file copy...")
            self._copy_files(path_id_dict, folder, self.gateway)

        if args.simple:
            self._fix_pixels_image_simple(ome, folder, md_fp)
        if args.barchive:
            print(f"Creating Bioimage Archive TSV at {md_fp}.")
            populate_tsv(src_datatype, ome, md_fp,
                         path_id_dict, folder)
        if args.rocrate:
            print(f"Creating RO-Crate metadata at {md_fp}.")
            populate_rocrate(src_datatype, ome, os.path.splitext(tar_path)[0],
                             path_id_dict, folder)
        if args.plugin:
            """
            Plugins for omero-cli-transfer can be created by providing
            an entry point with group name omero_cli_transfer.pack.plugin

            The entry point must be a function with following
            arguments:
              ome_object:  the omero object wrapper to pack
              destination_path: the path to export to
              tmp_path: the path where downloaded images and transfer.xml
                are located
              image_filenames_mapping: dict that maps image ids to filenames
            """
            from pkg_resources import iter_entry_points
            entry_points = []
            for p in iter_entry_points(group="omero_cli_transfer.pack.plugin"):
                if p.name == args.plugin:
                    entry_points.append(p.load())
            if len(entry_points) == 0:
                raise ValueError(f"Pack plugin {args.plugin} not found")
            else:
                assert len(entry_points) == 1
                pack_plugin_func = entry_points[0]
                pack_plugin_func(
                    ome_object=obj,
                    destination_path=Path(tar_path),
                    tmp_path=Path(folder),
                    image_filenames_mapping=path_id_dict,
                    conn=self.gateway)
        elif args.binaries == "all":
            self._package_files(os.path.splitext(tar_path)[0], args.zip,
                                folder)
            print("Cleaning up...")
            shutil.rmtree(folder)
        return

    def __unpack(self, args):
        self.metadata = []
        self._process_metadata(args.metadata)
        if not args.folder:
            print(f"Unzipping {args.filepath}...")
            hash, ome, folder = self._load_from_pack(args.filepath,
                                                     args.output)
        else:
            folder = Path(args.filepath)
            ome = from_xml(folder / "transfer.xml")
            hash = "imported from folder"
        print("Generating Image mapping and import filelist...")
        ome, src_img_map, filelist = self._create_image_map(ome)
        print("Importing data as orphans...")
        if args.ln_s_import:
            ln_s = True
        else:
            ln_s = False
        dest_img_map = self._import_files(folder, filelist,
                                          ln_s, args.skip, self.gateway)
        self._delete_all_rois(dest_img_map, self.gateway)
        print("Matching source and destination images...")
        img_map = self._make_image_map(src_img_map, dest_img_map, self.gateway)
        print("Creating and linking OMERO objects...")
        populate_omero(ome, img_map, self.gateway,
                       hash, folder, self.metadata, args.merge, args.figure)
        return

    def _load_from_pack(self, filepath: str, output: Optional[str] = None
                        ) -> Tuple[str, OME, Path]:
        if (not filepath) or (not isinstance(filepath, str)):
            raise TypeError("filepath must be a string")
        if output and not isinstance(output, str):
            raise TypeError("output folder must be a string")
        parent_folder = Path(filepath).parent
        filename = Path(filepath).resolve().stem
        if output:
            folder = Path(output)
        else:
            folder = parent_folder / filename
        if Path(filepath).exists():
            with open(filepath, 'rb') as file:
                md5 = hashlib.md5()
                while True:
                    data = file.read(MD5_BUF_SIZE)
                    if not data:
                        break
                    md5.update(data)
                hash = md5.hexdigest()
            if Path(filepath).suffix == '.zip':
                with ZipFile(filepath, 'r') as zipobj:
                    zipobj.extractall(str(folder))
            elif Path(filepath).suffix == '.tar':
                shutil.unpack_archive(filepath, str(folder), 'tar')
            else:
                raise ValueError("File is not a zip or tar file")
        else:
            raise FileNotFoundError("filepath is not a zip file")
        ome = from_xml(folder / "transfer.xml")
        return hash, ome, folder

    def _create_image_map(self, ome: OME
                          ) -> Tuple[OME, DefaultDict, List[str]]:
        if not (isinstance(ome, OME)):
            raise TypeError("XML is not valid OME format")
        img_map = DefaultDict(list)
        filelist = []
        newome = copy.deepcopy(ome)
        map_ref_ids = []
        for img in ome.images:
            fpath = get_server_path(img.annotation_refs,
                                    ome.structured_annotations)
            img_map[fpath].append(int(img.id.split(":")[-1]))
            # use XML path annotation instead
            if fpath.endswith('mock_folder'):
                filelist.append(fpath.rstrip("mock_folder"))
            else:
                filelist.append(fpath)
            for anref in img.annotation_refs:
                for an in newome.structured_annotations:
                    if anref.id == an.id and isinstance(an, XMLAnnotation):
                        tree = ETree.fromstring(to_xml(an.value,
                                                       canonicalize=True))
                        for el in tree:
                            if el.tag.rpartition('}')[2] == \
                                    "CLITransferServerPath":
                                newome.structured_annotations.remove(an)
                                map_ref_ids.append(an.id)
        for i in newome.images:
            for ref in i.annotation_refs:
                if ref.id in map_ref_ids:
                    i.annotation_refs.remove(ref)
        filelist = list(set(filelist))
        img_map = DefaultDict(list, {x: sorted(img_map[x])
                              for x in img_map.keys()})
        return newome, img_map, filelist

    def _import_files(self, folder: Path, filelist: List[str], ln_s: bool,
                      skip: str, gateway: BlitzGateway) -> dict:
        cli = CLI()
        cli.loadplugins()
        dest_map = {}
        curr_folder = str(Path('.').resolve())
        for filepath in filelist:
            dest_path = str(os.path.join(curr_folder, folder,  '.', filepath))
            command = ['import', dest_path]
            if ln_s:
                command.append('--transfer=ln_s')
            if skip:
                command.extend(['--skip', skip])
            cli.invoke(command)
            img_ids = self._get_image_ids(dest_path, gateway)
            dest_map[dest_path] = img_ids
        return dest_map

    def _delete_all_rois(self, dest_map: dict, gateway: BlitzGateway):
        roi_service = gateway.getRoiService()
        for imgs in dest_map.values():
            for img in imgs:
                result = roi_service.findByImage(img, None)
                for roi in result.rois:
                    gateway.deleteObject(roi)
        return

    def _get_image_ids(self, file_path: str, conn: BlitzGateway) -> List[str]:
        """Get the Ids of imported images.
        Note that this will not find images if they have not been imported.

        Returns
        -------
        image_ids : list of ints
            Ids of images imported from the specified client path, which
            itself is derived from ``file_path``.
        """
        q = conn.getQueryService()
        params = Parameters()
        path_query = str(file_path).strip('/')
        params.map = {"cpath": rstring('%s%%' % path_query)}
        results = q.projection(
            "SELECT i.id FROM Image i"
            " JOIN i.fileset fs"
            " JOIN fs.usedFiles u"
            " WHERE u.clientPath LIKE :cpath",
            params,
            conn.SERVICE_OPTS
            )
        all_image_ids = list(set(sorted([r[0].val for r in results])))
        image_ids = []
        for img_id in all_image_ids:
            anns = ezomero.get_map_annotation_ids(conn, "Image", img_id)
            if not anns:
                image_ids.append(img_id)
            else:
                is_annotated = False
                for ann in anns:
                    ann_content = conn.getObject("MapAnnotation", ann)
                    if ann_content.getNs() == \
                            'openmicroscopy.org/cli/transfer':
                        is_annotated = True
                if not is_annotated:
                    image_ids.append(img_id)
        return image_ids

    def _make_image_map(self, source_map: dict, dest_map: dict,
                        conn: Optional[BlitzGateway] = None) -> dict:
        # using both source and destination file-to-image-id maps,
        # map image IDs between source and destination
        src_dict = DefaultDict(list)
        imgmap = {}
        for k, v in source_map.items():
            if k.endswith("mock_folder"):
                newkey = k.rstrip("mock_folder")
                src_dict[newkey].extend(v)
            else:
                src_dict[k].extend(v)
        dest_dict = DefaultDict(list)
        for k, v in dest_map.items():
            newkey = k.split("/./")[-1]
            dest_dict[newkey].extend(v)
        src_dict = DefaultDict(list, {x: sorted(src_dict[x])
                                      for x in src_dict.keys()})
        dest_dict = DefaultDict(list, {x: sorted(dest_dict[x])
                                       for x in dest_dict.keys()})
        for src_k in src_dict.keys():
            src_v = src_dict[src_k]
            if src_k in dest_dict.keys():
                dest_v = dest_dict[src_k]
                clean_dest = []
                if not conn:
                    clean_dest = dest_v
                else:
                    for i in dest_v:
                        img_obj = conn.getObject("Image", i)
                        anns = 0
                        for j in img_obj.listAnnotations():
                            ns = j.getNs()
                            if ns.startswith(
                                    "openmicroscopy.org/cli/transfer"):
                                anns += 1
                        if not anns:
                            clean_dest.append(i)
                if len(src_v) == len(clean_dest):
                    for count in range(len(src_v)):
                        map_key = f"Image:{src_v[count]}"
                        imgmap[map_key] = clean_dest[count]
        return imgmap

    def __prepare(self, args):
        populate_xml_folder(args.folder, args.filelist, self.gateway,
                            self.session)
        return


try:
    register("transfer", TransferControl, HELP)
except NameError:
    if __name__ == "__main__":
        cli = CLI()
        cli.register("transfer", TransferControl, HELP)
        cli.invoke(sys.argv[1:])
