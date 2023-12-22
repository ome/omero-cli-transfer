# Copyright (C) 2022 The Jackson Laboratory
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

from ome_types import to_xml, OME, from_xml
from ome_types.model import Project, ProjectRef
from ome_types.model import Screen
from ome_types.model.screen import PlateRef
from ome_types.model import Well, WellSample
from ome_types.model import Plate
from ome_types.model import Dataset, DatasetRef
from ome_types.model import Image, ImageRef, Pixels
from ome_types.model import TagAnnotation, MapAnnotation, ROI, XMLAnnotation
from ome_types.model import FileAnnotation, BinaryFile, BinData
from ome_types.model import AnnotationRef, ROIRef, Map
from ome_types.model import CommentAnnotation, LongAnnotation
from ome_types.model import Point, Line, Rectangle, Ellipse, Polygon
from ome_types.model import Polyline, Label, Shape
from ome_types.model.map import M
from omero.sys import Parameters
from omero.gateway import BlitzGateway
from omero.model import TagAnnotationI, MapAnnotationI, FileAnnotationI
from omero.model import CommentAnnotationI, LongAnnotationI, Fileset
from omero.model import PointI, LineI, RectangleI, EllipseI, PolygonI
from omero.model import PolylineI, LabelI, ImageI, RoiI, IObject
from omero.model import DatasetI, ProjectI, ScreenI, PlateI, WellI, Annotation
from omero.cli import CLI
from typing import Tuple, List, Optional, Union, Any, Dict, TextIO
from subprocess import PIPE, DEVNULL
from generate_omero_objects import get_server_path
import xml.etree.cElementTree as ETree
from os import PathLike
import pkg_resources
import ezomero
import os
import csv
import base64
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import shutil
import copy

ann_count = 0


def create_proj_and_ref(**kwargs) -> Tuple[Project, ProjectRef]:
    proj = Project(**kwargs)
    proj_ref = ProjectRef(id=proj.id)
    return proj, proj_ref


def create_plate_and_ref(**kwargs) -> Tuple[Plate, PlateRef]:
    pl = Plate(**kwargs)
    pl_ref = PlateRef(id=pl.id)
    return pl, pl_ref


def create_screen(**kwargs) -> Screen:
    scr = Screen(**kwargs)
    return scr


def create_dataset_and_ref(**kwargs) -> Tuple[Dataset, DatasetRef]:
    ds = Dataset(**kwargs)
    ds_ref = DatasetRef(id=ds.id)
    return ds, ds_ref


def create_pixels(obj: ImageI) -> Pixels:
    # we're assuming a single Pixels object per image
    pix_obj = obj.getPrimaryPixels()
    pixels = Pixels(
        id=obj.getId(),
        dimension_order=pix_obj.getDimensionOrder().getValue(),
        size_c=pix_obj.getSizeC(),
        size_t=pix_obj.getSizeT(),
        size_x=pix_obj.getSizeX(),
        size_y=pix_obj.getSizeY(),
        size_z=pix_obj.getSizeZ(),
        type=pix_obj.getPixelsType().getValue(),
        metadata_only=True)
    return pixels


def create_image_and_ref(**kwargs) -> Tuple[Image, ImageRef]:
    img = Image(**kwargs)
    img_ref = ImageRef(id=img.id)
    return img, img_ref


def create_tag_and_ref(**kwargs) -> Tuple[TagAnnotation, AnnotationRef]:
    tag = TagAnnotation(**kwargs)
    tagref = AnnotationRef(id=tag.id)
    return tag, tagref


def create_comm_and_ref(**kwargs) -> Tuple[CommentAnnotation, AnnotationRef]:
    tag = CommentAnnotation(**kwargs)
    tagref = AnnotationRef(id=tag.id)
    return tag, tagref


def create_kv_and_ref(**kwargs) -> Tuple[MapAnnotation, AnnotationRef]:
    kv = MapAnnotation(**kwargs)
    kvref = AnnotationRef(id=kv.id)
    return kv, kvref


def create_xml_and_ref(**kwargs) -> Tuple[XMLAnnotation, AnnotationRef]:
    xml = XMLAnnotation(**kwargs)
    xmlref = AnnotationRef(id=xml.id)
    return xml, xmlref


def create_long_and_ref(**kwargs) -> Tuple[LongAnnotation, AnnotationRef]:
    long = LongAnnotation(**kwargs)
    longref = AnnotationRef(id=long.id)
    return long, longref


def create_roi_and_ref(**kwargs) -> Tuple[ROI, ROIRef]:
    roi = ROI(**kwargs)
    roiref = ROIRef(id=roi.id)
    return roi, roiref


def create_file_ann_and_ref(**kwargs) -> Tuple[FileAnnotation, AnnotationRef]:
    file_ann = FileAnnotation(**kwargs)
    file_ann_ref = AnnotationRef(id=file_ann.id)
    return file_ann, file_ann_ref


def create_point(shape: PointI) -> Point:
    args = {'id': shape.getId().val, 'x': shape.getX().val,
            'y': shape.getY().val}
    args['text'] = ''
    args['the_c'] = 0
    args['the_z'] = 0
    args['the_t'] = 0
    if shape.getTextValue() is not None:
        args['text'] = shape.getTextValue().val
    if shape.getTheC() is not None:
        args['the_c'] = max(shape.getTheC().val, 0)
    if shape.getTheZ() is not None:
        args['the_z'] = shape.getTheZ().val
    if shape.getTheT() is not None:
        args['the_t'] = shape.getTheT().val
    if shape.getFillColor() is not None:
        args['fill_color'] = shape.getFillColor().val
    if shape.getLocked() is not None:
        args['locked'] = shape.getLocked().val
    if shape.getStrokeColor() is not None:
        args['stroke_color'] = shape.getStrokeColor().val
    if shape.getStrokeWidth() is not None:
        args['stroke_width'] = shape.getStrokeWidth().getValue()
    pt = Point(**args)
    return pt


def create_line(shape: LineI) -> Line:
    args = {'id': shape.getId().val, 'x1': shape.getX1().val,
            'y1': shape.getY1().val, 'x2': shape.getX2().val,
            'y2': shape.getY2().val}
    args['text'] = ''
    args['the_c'] = 0
    args['the_z'] = 0
    args['the_t'] = 0
    if shape.getTextValue() is not None:
        args['text'] = shape.getTextValue().val
    if shape.getTheC() is not None:
        args['the_c'] = max(shape.getTheC().val, 0)
    if shape.getTheZ() is not None:
        args['the_z'] = shape.getTheZ().val
    if shape.getTheT() is not None:
        args['the_t'] = shape.getTheT().val
    if shape.getFillColor() is not None:
        args['fill_color'] = shape.getFillColor().val
    if shape.getLocked() is not None:
        args['locked'] = shape.getLocked().val
    if shape.getStrokeColor() is not None:
        args['stroke_color'] = shape.getStrokeColor().val
    if shape.getStrokeWidth() is not None:
        args['stroke_width'] = shape.getStrokeWidth().getValue()
    if shape.getMarkerStart() is not None:
        args['marker_start'] = shape.getMarkerStart().val
    if shape.getMarkerEnd() is not None:
        args['marker_end'] = shape.getMarkerEnd().val
    ln = Line(**args)
    return ln


def create_rectangle(shape: RectangleI) -> Rectangle:
    args = {'id': shape.getId().val, 'x': shape.getX().val,
            'y': shape.getY().val, 'height': shape.getHeight().val,
            'width': shape.getWidth().val}
    args['text'] = ''
    args['the_c'] = 0
    args['the_z'] = 0
    args['the_t'] = 0
    if shape.getTextValue() is not None:
        args['text'] = shape.getTextValue().val
    if shape.getTheC() is not None:
        args['the_c'] = max(shape.getTheC().val, 0)
    if shape.getTheZ() is not None:
        args['the_z'] = shape.getTheZ().val
    if shape.getTheT() is not None:
        args['the_t'] = shape.getTheT().val
    if shape.getFillColor() is not None:
        args['fill_color'] = shape.getFillColor().val
    if shape.getLocked() is not None:
        args['locked'] = shape.getLocked().val
    if shape.getStrokeColor() is not None:
        args['stroke_color'] = shape.getStrokeColor().val
    if shape.getStrokeWidth() is not None:
        args['stroke_width'] = shape.getStrokeWidth().getValue()
    rec = Rectangle(**args)
    return rec


def create_ellipse(shape: EllipseI) -> Ellipse:
    args = {'id': shape.getId().val, 'x': shape.getX().val,
            'y': shape.getY().val, 'radius_x': shape.getRadiusX().val,
            'radius_y': shape.getRadiusY().val}
    args['text'] = ''
    args['the_c'] = 0
    args['the_z'] = 0
    args['the_t'] = 0
    if shape.getTextValue() is not None:
        args['text'] = shape.getTextValue().val
    if shape.getTheC() is not None:
        args['the_c'] = max(shape.getTheC().val, 0)
    if shape.getTheZ() is not None:
        args['the_z'] = shape.getTheZ().val
    if shape.getTheT() is not None:
        args['the_t'] = shape.getTheT().val
    if shape.getFillColor() is not None:
        args['fill_color'] = shape.getFillColor().val
    if shape.getLocked() is not None:
        args['locked'] = shape.getLocked().val
    if shape.getStrokeColor() is not None:
        args['stroke_color'] = shape.getStrokeColor().val
    if shape.getStrokeWidth() is not None:
        args['stroke_width'] = shape.getStrokeWidth().getValue()
    ell = Ellipse(**args)
    return ell


def create_polygon(shape: PolygonI) -> Polygon:
    args = {'id': shape.getId().val, 'points': shape.getPoints().val}
    args['text'] = ''
    args['the_c'] = 0
    args['the_z'] = 0
    args['the_t'] = 0
    if shape.getTextValue() is not None:
        args['text'] = shape.getTextValue().val
    if shape.getTheC() is not None:
        args['the_c'] = max(shape.getTheC().val, 0)
    if shape.getTheZ() is not None:
        args['the_z'] = shape.getTheZ().val
    if shape.getTheT() is not None:
        args['the_t'] = shape.getTheT().val
    if shape.getFillColor() is not None:
        args['fill_color'] = shape.getFillColor().val
    if shape.getLocked() is not None:
        args['locked'] = shape.getLocked().val
    if shape.getStrokeColor() is not None:
        args['stroke_color'] = shape.getStrokeColor().val
    if shape.getStrokeWidth() is not None:
        args['stroke_width'] = shape.getStrokeWidth().getValue()
    pol = Polygon(**args)
    return pol


def create_polyline(shape: PolylineI) -> Polyline:
    args = {'id': shape.getId().val, 'points': shape.getPoints().val}
    args['text'] = ''
    args['the_c'] = 0
    args['the_z'] = 0
    args['the_t'] = 0
    if shape.getTextValue() is not None:
        args['text'] = shape.getTextValue().val
    if shape.getTheC() is not None:
        args['the_c'] = max(shape.getTheC().val, 0)
    if shape.getTheZ() is not None:
        args['the_z'] = shape.getTheZ().val
    if shape.getTheT() is not None:
        args['the_t'] = shape.getTheT().val
    if shape.getFillColor() is not None:
        args['fill_color'] = shape.getFillColor().val
    if shape.getLocked() is not None:
        args['locked'] = shape.getLocked().val
    if shape.getStrokeColor() is not None:
        args['stroke_color'] = shape.getStrokeColor().val
    if shape.getStrokeWidth() is not None:
        args['stroke_width'] = shape.getStrokeWidth().getValue()
    pol = Polyline(**args)
    return pol


def create_label(shape: LabelI) -> Label:
    args = {'id': shape.getId().val, 'x': shape.getX().val,
            'y': shape.getY().val}
    args['text'] = shape.getTextValue().val
    args['font_size'] = 10
    args['the_c'] = 0
    args['the_z'] = 0
    args['the_t'] = 0
    if shape.getFontSize() is not None:
        args['font_size'] = shape.getFontSize().getValue()
    if shape.getTheC() is not None:
        args['the_c'] = max(shape.getTheC().val, 0)
    if shape.getTheZ() is not None:
        args['the_z'] = shape.getTheZ().val
    if shape.getTheT() is not None:
        args['the_t'] = shape.getTheT().val
    if shape.getFillColor() is not None:
        args['fill_color'] = shape.getFillColor().val
    if shape.getLocked() is not None:
        args['locked'] = shape.getLocked().val
    if shape.getStrokeColor() is not None:
        args['stroke_color'] = shape.getStrokeColor().val
    if shape.getStrokeWidth() is not None:
        args['stroke_width'] = shape.getStrokeWidth().getValue()
    pt = Label(**args)
    return pt


def create_shapes(roi: RoiI) -> List[Shape]:
    shapes: List[Shape] = []
    for s in roi.iterateShapes():
        if isinstance(s, PointI):
            p = create_point(s)
            shapes.append(p)
        elif isinstance(s, LineI):
            line = create_line(s)
            shapes.append(line)
        elif isinstance(s, RectangleI):
            r = create_rectangle(s)
            shapes.append(r)
        elif isinstance(s, EllipseI):
            e = create_ellipse(s)
            shapes.append(e)
        elif isinstance(s, PolygonI):
            pol = create_polygon(s)
            shapes.append(pol)
        elif isinstance(s, PolylineI):
            polline = create_polyline(s)
            shapes.append(polline)
        elif isinstance(s, LabelI):
            lab = create_label(s)
            shapes.append(lab)
        else:
            print("not a supported ROI type")
            continue
    return shapes


def create_filepath_annotations(id: str, conn: BlitzGateway,
                                simple: bool,
                                filename: Union[str, PathLike] = ".",
                                plate_path: Optional[str] = None,
                                ds: Optional[str] = None,
                                proj: Optional[str] = None,
                                ) -> Tuple[List[XMLAnnotation],
                                           List[AnnotationRef]]:
    global ann_count
    ns = 'openmicroscopy.org/cli/transfer'
    anns = []
    anrefs = []
    fp_type = id.split(":")[0]
    clean_id = int(id.split(":")[-1])
    if not ds:
        ds = ""
    if not proj:
        proj = ""
    if fp_type == "Image":
        fpaths = ezomero.get_original_filepaths(conn, clean_id)
        if len(fpaths) > 1:
            if not simple:
                allpaths = []
                for f in fpaths:
                    f = Path(f)
                    allpaths.append(f.parts)
                common_root = Path(*os.path.commonprefix(allpaths))
            else:
                common_root = "./"
                common_root = Path(common_root) / proj / ds
            path = os.path.join(common_root, 'mock_folder')
            xml = create_path_xml(path)
            an, anref = create_xml_and_ref(id=ann_count,
                                           namespace=ns,
                                           value=xml)
            anns.append(an)
            ann_count += 1
            anref = AnnotationRef(id=an.id)
            anrefs.append(anref)
        else:
            if simple:
                common_root = "./"
            if fpaths:
                f = fpaths[0]
                if simple:
                    filename = Path(f).name
                    f = Path(common_root) / proj / ds / filename
                xml = create_path_xml(str(f))
                an, anref = create_xml_and_ref(id=ann_count,
                                               namespace=ns,
                                               value=xml)
                anns.append(an)
                ann_count += 1
                anref = AnnotationRef(id=an.id)
                anrefs.append(anref)
            else:
                f = f'pixel_images/{clean_id}.tiff'
                if simple:
                    f = f'{clean_id}.tiff'
                    f = Path(common_root) / proj / ds / f
                    xml = create_path_xml(str(f))
                    an, anref = create_xml_and_ref(id=ann_count,
                                                   namespace=ns,
                                                   value=xml)
                    anns.append(an)
                    ann_count += 1
                    anref = AnnotationRef(id=an.id)
                    anrefs.append(anref)
                xml = create_path_xml(str(f))
                an, anref = create_xml_and_ref(id=ann_count,
                                               namespace=ns,
                                               value=xml)
                anns.append(an)
                ann_count += 1
                anref = AnnotationRef(id=an.id)
                anrefs.append(anref)

    elif fp_type == "Annotation":
        filename = str(Path(filename).name)
        f = f'file_annotations/{clean_id}/{filename}'
        xml = create_path_xml(str(f))
        an, anref = create_xml_and_ref(id=ann_count,
                                       namespace=ns,
                                       value=xml)
        anns.append(an)
        ann_count += 1
        anref = AnnotationRef(id=an.id)
        anrefs.append(anref)
    elif fp_type == "Plate":
        xml = create_path_xml(plate_path)
        an, anref = create_xml_and_ref(id=ann_count,
                                       namespace=ns,
                                       value=xml)
        anns.append(an)
        ann_count += 1
        anref = AnnotationRef(id=an.id)
        anrefs.append(anref)
    return anns, anrefs


def create_figure_annotations(id: str) -> Tuple[XMLAnnotation,
                                                AnnotationRef]:
    ns = id
    global ann_count
    clean_id = int(ns.split(":")[-1])
    f = f'figures/Figure_{clean_id}.json'
    xml = create_path_xml(str(f))
    an, anref = create_xml_and_ref(id=ann_count,
                                   namespace=ns,
                                   value=xml)
    ann_count += 1
    return (an, anref)


def create_provenance_metadata(conn: BlitzGateway, img_id: int,
                               hostname: str,
                               metadata: Union[List[str], None], plate: bool
                               ) -> Union[Tuple[MapAnnotation, AnnotationRef],
                                          Tuple[None, None]]:
    global ann_count
    if not metadata:
        return None, None
    software = "omero-cli-transfer"
    version = pkg_resources.get_distribution(software).version
    date_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    ns = 'openmicroscopy.org/cli/transfer'
    curr_user = conn.getUser().getName()
    curr_group = conn.getGroupFromContext().getName()
    db_id = conn.getConfigService().getDatabaseUuid()

    md_dict: Dict[str, Any] = {}
    if plate:
        if "plate_id" in metadata:
            md_dict['origin_plate_id'] = img_id
    else:
        if "img_id" in metadata:
            md_dict['origin_image_id'] = img_id
    if "timestamp" in metadata:
        md_dict['packing_timestamp'] = date_time
    if "software" in metadata:
        md_dict['software'] = software
    if "version" in metadata:
        md_dict['version'] = version
    if "hostname" in metadata:
        md_dict['origin_hostname'] = hostname
    if "md5" in metadata:
        md_dict['md5'] = "TBC"
    if "orig_user" in metadata:
        md_dict['original_user'] = curr_user
    if "orig_group" in metadata:
        md_dict['original_group'] = curr_group
    if "db_id" in metadata:
        md_dict['database_id'] = db_id
    xml = create_metadata_xml(md_dict)
    an, anref = create_xml_and_ref(id=ann_count,
                                   namespace=ns,
                                   value=xml)
    ann_count += 1
    return an, anref


def create_objects(folder, filelist):
    img_files = []
    cli = CLI()
    cli.loadplugins()
    par_folder = Path(folder).parent
    if not filelist:
        for path, subdirs, files in os.walk(folder):
            for f in files:
                img_files.append(os.path.relpath(
                                            os.path.join(path, f), folder))
        targets = copy.deepcopy(img_files)
        for img in img_files:
            if img not in (targets):
                continue
            img_path = os.path.join(os.getcwd(), folder, img)
            cmd = ["omero", 'import', '-f', img_path, "\n"]
            res = cli.popen(cmd, stdout=PIPE, stderr=DEVNULL)
            std = res.communicate()
            files = parse_files_import(std[0].decode('UTF-8'), folder)
            if len(files) > 1:
                for f in files:
                    targets.remove(f)
                targets.append(img)
            if len(files) == 0:
                targets.remove(img)
    else:
        # should make relative paths here
        with open(folder, "r") as f:
            targets_str = f.read().splitlines()
        targets = []
        for target in targets_str:
            if target.startswith("/"):
                targets.append(os.path.relpath(target, par_folder))
            else:
                targets.append(target)
            # targets.append(str((par_folder / target).resolve()))
    images = []
    plates = []
    annotations = []
    counter_imgs = 1
    counter_pls = 1
    counter_anns = 1
    for target in targets:
        if filelist:
            folder = par_folder
        target_full = os.path.join(os.getcwd(), folder, target)
        print(f"Processing file {Path(target_full).resolve()}")
        res = run_showinf(target_full, cli)
        if filelist:
            folder = par_folder
        imgs, pls, anns = parse_showinf(res, counter_imgs, counter_pls,
                                        counter_anns, target, folder)
        images.extend(imgs)
        counter_imgs = counter_imgs + len(imgs)
        plates.extend(pls)
        counter_pls = counter_pls + len(pls)
        annotations.extend(anns)
        counter_anns = counter_anns + len(anns)
    return images, plates, annotations


def run_showinf(target, cli):
    cmd = ["showinf", target, '-nopix', '-omexml-only',
           '-no-sas', '-noflat']
    res = cli.popen(cmd, stdout=PIPE, stderr=DEVNULL)
    std = res.communicate()
    return std[0].decode('UTF-8')


def parse_files_import(text, folder):
    lines = text.split("\n")
    targets = [line for line in lines if not line.startswith("#")
               and len(line) > 0]
    clean_targets = []
    for target in targets:
        clean = os.path.relpath(target, folder)
        clean_targets.append(clean)
    return clean_targets


def parse_showinf(text, counter_imgs, counter_plates, counter_ann,
                  target, folder):
    ome = from_xml(text)
    images = []
    plates = []
    annotations = []
    img_id = counter_imgs
    pl_id = counter_plates
    ann_id = counter_ann
    img_ref = {}
    for image in ome.images:
        img_id_str = f"Image:{str(img_id)}"
        img_ref[image.id] = img_id_str
        pix = create_empty_pixels(image, img_id)
        if len(ome.images) > 1:  # differentiating names
            if image.name == "":
                image_name = "0"
            else:
                image_name = image.name
            filename = Path(target).name
            img = Image(id=img_id_str, name=filename + " [" + image_name + "]",
                        pixels=pix)
        else:
            img = Image(id=img_id_str, name=image.name, pixels=pix)
        img_id += 1
        xml = create_path_xml(target)
        ns = 'openmicroscopy.org/cli/transfer'
        an, anref = create_xml_and_ref(id=ann_id,
                                       namespace=ns,
                                       value=xml)
        annotations.append(an)
        ann_id += 1
        anref = AnnotationRef(id=an.id)
        img.annotation_refs.append(anref)
        an, anref = create_prepare_metadata(ann_id)
        annotations.append(an)
        ann_id += 1
        img.annotation_refs.append(anref)
        images.append(img)
    for plate in ome.plates:
        pl_id_str = f"Plate:{str(pl_id)}"
        pl = Plate(id=pl_id_str, name=plate.name, wells=plate.wells)
        for w in pl.wells:
            for ws in w.well_samples:
                ws.image_ref.id = img_ref[ws.image_ref.id]
        pl_id += 1
        xml = create_path_xml(target)
        an, anref = create_xml_and_ref(id=ann_id,
                                       namespace=ns,
                                       value=xml)
        annotations.append(an)
        anref = AnnotationRef(id=an.id)
        pl.annotation_refs.append(anref)
        plates.append(pl)
    return images, plates, annotations


def create_path_xml(target):
    base = ETree.Element("CLITransferServerPath", attrib={
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation":
        "https://raw.githubusercontent.com/ome/omero-cli-transfer/"
        "main/schemas/serverpath.xsd"})
    ETree.SubElement(base, "Path").text = target
    return ETree.tostring(base, encoding='unicode')


def create_prepare_metadata(ann_id):
    software = "omero-cli-transfer"
    version = pkg_resources.get_distribution(software).version
    date_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    ns = 'openmicroscopy.org/cli/transfer/prepare'
    md_dict: Dict[str, Any] = {}
    md_dict['software'] = software
    md_dict['version'] = version
    md_dict['packing_timestamp'] = date_time
    xml = create_metadata_xml(md_dict)
    xml_ann, ref = create_xml_and_ref(id=ann_id,
                                      namespace=ns,
                                      value=xml)
    return xml_ann, ref


def create_metadata_xml(metadata):
    base = ETree.Element("CLITransferMetadata", attrib={
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation":
        "https://raw.githubusercontent.com/ome/omero-cli-transfer/"
        "main/schemas/preparemetadata.xsd"})
    for _key, _value in metadata.items():
        ETree.SubElement(base, _key).text = str(_value)
    return ETree.tostring(base, encoding='unicode')


def create_empty_pixels(image, id):
    pix_id = f"Pixels:{str(id)}"
    pixels = Pixels(
        id=pix_id,
        dimension_order=image.pixels.dimension_order,
        size_c=image.pixels.size_c,
        size_t=image.pixels.size_t,
        size_x=image.pixels.size_x,
        size_y=image.pixels.size_y,
        size_z=image.pixels.size_z,
        type=image.pixels.type,
        metadata_only=True)
    return pixels


def populate_roi(obj: RoiI, roi_obj: IObject, ome: OME, conn: BlitzGateway
                 ) -> Union[ROIRef, None]:
    id = obj.getId().getValue()
    name = obj.getName()
    if name is not None:
        name = name.getValue()
    desc = obj.getDescription()
    if desc is not None:
        desc = desc.getValue()
    shapes = create_shapes(obj)
    if not shapes:
        return None
    roi, roi_ref = create_roi_and_ref(id=id, name=name, description=desc,
                                      union=shapes)
    for ann in roi_obj.listAnnotations():
        add_annotation(roi, ann, ome, conn)
    if roi not in ome.rois:
        ome.rois.append(roi)
    return roi_ref


def populate_image(obj: ImageI, ome: OME, conn: BlitzGateway, hostname: str,
                   metadata: List[str], simple: bool,
                   fset: Union[None, Fileset] = None,
                   ds: Optional[str] = None, proj: Optional[str] = None,
                   ) -> ImageRef:
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    img_id = f"Image:{str(id)}"
    if img_id in [i.id for i in ome.images]:
        img_ref = ImageRef(id=img_id)
        return img_ref
    pix = create_pixels(obj)
    img, img_ref = create_image_and_ref(id=id, name=name,
                                        description=desc, pixels=pix)
    for ann in obj.listAnnotations():
        add_annotation(img, ann, ome, conn)
    kv, ref = create_provenance_metadata(conn, id, hostname, metadata, False)
    if kv:
        kv_id = f"Annotation:{str(kv.id)}"
        if kv_id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(kv)
        if ref:
            img.annotation_refs.append(ref)
    filepath_anns, refs = create_filepath_annotations(img_id, conn,
                                                      simple, ds=ds,
                                                      proj=proj)
    for i in range(len(filepath_anns)):
        ome.structured_annotations.append(filepath_anns[i])
        img.annotation_refs.append(refs[i])
    roi_service = conn.getRoiService()
    rois = roi_service.findByImage(id, None).rois
    for roi in rois:
        roi_obj = conn.getObject('Roi', roi.getId().getValue())
        roi_ref = populate_roi(roi, roi_obj, ome, conn)
        if not roi_ref:
            continue
        img.roi_ref.append(roi_ref)
    img_id = f"Image:{str(img.id)}"
    if img_id not in [i.id for i in ome.datasets]:
        ome.images.append(img)
    if not fset:
        fset = obj.getFileset()
    if fset:
        for fs_image in fset.copyImages():
            fs_img_id = f"Image:{str(fs_image.getId())}"
            if fs_img_id not in [i.id for i in ome.images]:
                populate_image(fs_image, ome, conn, hostname, metadata,
                               simple, fset)
    return img_ref


def populate_dataset(obj: DatasetI, ome: OME, conn: BlitzGateway,
                     hostname: str, metadata: List[str], simple: bool,
                     proj: Optional[str] = None,
                     ) -> DatasetRef:
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    ds, ds_ref = create_dataset_and_ref(id=id, name=name,
                                        description=desc)
    for ann in obj.listAnnotations():
        add_annotation(ds, ann, ome, conn)
    for img in obj.listChildren():
        img_obj = conn.getObject('Image', img.getId())
        img_ref = populate_image(img_obj, ome, conn, hostname, metadata,
                                 simple, ds=str(id) + "_" + name,
                                 proj=proj)
        ds.image_refs.append(img_ref)
    ds_id = f"Dataset:{str(ds.id)}"
    if ds_id not in [i.id for i in ome.datasets]:
        ome.datasets.append(ds)
    return ds_ref


def populate_project(obj: ProjectI, ome: OME, conn: BlitzGateway,
                     hostname: str, metadata: List[str], simple: bool):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    proj, _ = create_proj_and_ref(id=id, name=name, description=desc)
    for ann in obj.listAnnotations():
        add_annotation(proj, ann, ome, conn)

    for ds in obj.listChildren():
        ds_obj = conn.getObject('Dataset', ds.getId())
        ds_ref = populate_dataset(ds_obj, ome, conn, hostname, metadata,
                                  simple, proj=str(id) + "_" + name)

        proj.dataset_refs.append(ds_ref)
    ome.projects.append(proj)


def populate_screen(obj: ScreenI, ome: OME, conn: BlitzGateway,
                    hostname: str, metadata: List[str]):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    scr = create_screen(id=id, name=name, description=desc)
    for ann in obj.listAnnotations():
        add_annotation(scr, ann, ome, conn)
    for pl in obj.listChildren():
        pl_obj = conn.getObject('Plate', pl.getId())
        pl_ref = populate_plate(pl_obj, ome, conn, hostname, metadata)
        scr.plate_refs.append(pl_ref)
    ome.screens.append(scr)


def populate_plate(obj: PlateI, ome: OME, conn: BlitzGateway,
                   hostname: str, metadata: List[str]) -> PlateRef:
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    print(f"populating plate {id}")
    pl, pl_ref = create_plate_and_ref(id=id, name=name, description=desc)
    for ann in obj.listAnnotations():
        add_annotation(pl, ann, ome, conn)
    kv, ref = create_provenance_metadata(conn, id, hostname, metadata, True)
    if kv:
        kv_id = f"Annotation:{str(kv.id)}"
        if kv_id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(kv)
        if ref:
            pl.annotation_refs.append(ref)
    for well in obj.listChildren():
        well_obj = conn.getObject('Well', well.getId())
        well_ref = populate_well(well_obj, ome, conn, hostname, metadata)
        pl.wells.append(well_ref)

    # this will need some changing to tackle XMLs
    last_image_anns = ome.images[-1].annotation_refs
    plate_path = get_server_path(last_image_anns, ome.structured_annotations)
    filepath_anns, refs = create_filepath_annotations(pl.id, conn,
                                                      simple=False,
                                                      plate_path=plate_path)
    for i in range(len(filepath_anns)):
        ome.structured_annotations.append(filepath_anns[i])
        pl.annotation_refs.append(refs[i])
    pl_id = f"Plate:{str(pl.id)}"
    if pl_id not in [i.id for i in ome.plates]:
        ome.plates.append(pl)
    return pl_ref


def populate_well(obj: WellI, ome: OME, conn: BlitzGateway,
                  hostname: str, metadata: List[str]) -> Well:
    id = obj.getId()
    column = obj.getColumn()
    row = obj.getRow()
    print(f"populating well {id}")
    samples = []
    for index in range(obj.countWellSample()):
        ws_obj = obj.getWellSample(index)
        ws_id = ws_obj.getId()
        ws_img = ws_obj.getImage()
        ws_img_ref = populate_image(ws_img, ome, conn, hostname, metadata,
                                    simple=False)
        ws_index = int(ws_img_ref.id.split(":")[-1])
        ws = WellSample(id=ws_id, index=ws_index, image_ref=ws_img_ref)
        samples.append(ws)
    well = Well(id=id, row=row, column=column, well_samples=samples)
    for ann in obj.listAnnotations():
        add_annotation(well, ann, ome, conn)
    return well


def add_annotation(obj: Union[Project, Dataset, Image, Plate, Screen,
                              Well, ROI],
                   ann: Annotation, ome: OME, conn: BlitzGateway):
    if ann.OMERO_TYPE == TagAnnotationI:
        tag, ref = create_tag_and_ref(id=ann.getId(),
                                      value=ann.getTextValue())
        if tag.id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(tag)
        obj.annotation_ref.append(ref)

    elif ann.OMERO_TYPE == MapAnnotationI:
        mmap = []
        for _key, _value in ann.getMapValueAsMap().items():
            if _value:
                mmap.append(M(k=_key, value=str(_value)))
            else:
                mmap.append(M(k=_key, value=''))
        kv, ref = create_kv_and_ref(id=ann.getId(),
                                    namespace=ann.getNs(),
                                    value=Map(
                                    ms=mmap))
        if kv.id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(kv)
        obj.annotation_ref.append(ref)

    elif ann.OMERO_TYPE == CommentAnnotationI:
        comm, ref = create_comm_and_ref(id=ann.getId(),
                                        value=ann.getTextValue())
        if comm.id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(comm)
        obj.annotation_ref.append(ref)

    elif ann.OMERO_TYPE == LongAnnotationI:
        long, ref = create_long_and_ref(id=ann.getId(),
                                        namespace=ann.getNs(),
                                        value=ann.getValue())
        if long.id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(long)
        obj.annotation_ref.append(ref)

    elif ann.OMERO_TYPE == FileAnnotationI:
        contents = ann.getFile().getPath().encode()
        b64 = base64.b64encode(contents)
        length = len(b64)
        fpath = os.path.join(ann.getFile().getPath(), ann.getFile().getName())
        binaryfile = BinaryFile(file_name=fpath,
                                size=ann.getFile().getSize(),
                                bin_data=BinData(big_endian=True,
                                                 length=length,
                                                 value=b64
                                                 )
                                )
        f, ref = create_file_ann_and_ref(id=ann.getId(),
                                         namespace=ann.getNs(),
                                         binary_file=binaryfile)
        filepath_anns, refs = create_filepath_annotations(
                                f.id,
                                conn,
                                simple=False,
                                filename=ann.getFile().getName())
        for i in range(len(filepath_anns)):
            ome.structured_annotations.append(filepath_anns[i])
            f.annotation_ref.append(refs[i])
        if f.id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(f)
        obj.annotation_ref.append(ref)


def list_file_ids(ome: OME) -> dict:
    id_list = {}
    for img in ome.images:
        path = get_server_path(img.annotation_refs, ome.structured_annotations)
        id_list[img.id] = path
    for ann in ome.structured_annotations:
        if isinstance(ann, FileAnnotation):
            if ann.namespace != "omero.web.figure.json":
                path = get_server_path(ann.annotation_refs,
                                       ome.structured_annotations)
            id_list[ann.id] = path
    return id_list


def populate_xml(datatype: str, id: int, filepath: str, conn: BlitzGateway,
                 hostname: str, barchive: bool, simple: bool, figure: bool,
                 metadata: List[str]) -> Tuple[OME, dict]:
    ome = OME()
    global ann_count
    ann_count = uuid4().int >> 64
    obj = conn.getObject(datatype, id)
    if datatype == 'Project':
        populate_project(obj, ome, conn, hostname, metadata, simple)
    elif datatype == 'Dataset':
        populate_dataset(obj, ome, conn, hostname, metadata, simple)
    elif datatype == 'Image':
        populate_image(obj, ome, conn, hostname, metadata, simple)
    elif datatype == 'Screen':
        populate_screen(obj, ome, conn, hostname, metadata)
    elif datatype == 'Plate':
        populate_plate(obj, ome, conn, hostname, metadata)
    if (not (barchive or simple)) and figure:
        populate_figures(ome, conn, filepath)
    if not barchive:
        with open(filepath, 'w') as fp:
            print(to_xml(ome), file=fp)
            fp.close()
    path_id_dict = list_file_ids(ome)
    return ome, path_id_dict


def populate_xml_folder(folder: str, filelist: bool, conn: BlitzGateway,
                        session: str) -> Tuple[OME, dict]:
    ome = OME()
    images, plates, annotations = create_objects(folder, filelist)
    ome.images = images
    ome.plates = plates
    ome.structured_annotations = annotations
    if filelist:
        filepath = str(Path(folder).parent.resolve() / "transfer.xml")
    else:
        if Path(folder).exists():
            filepath = str(Path(folder) / "transfer.xml")
        else:
            raise ValueError("Folder cannot be found!")
    with open(filepath, 'w') as fp:
        print(to_xml(ome), file=fp)
        fp.close()
    path_id_dict = list_file_ids(ome)
    return ome, path_id_dict


def populate_tsv(datatype: str, ome: OME, filepath: str,
                 path_id_dict: dict, folder: str):
    if datatype == "Plate" or datatype == "Screen":
        print("Bioimage Archive export of Plate/Screen currently unsupported")
        return
    with open(filepath, 'w') as fp:
        write_lines(datatype, ome, fp, path_id_dict, folder)
        fp.close()
    return


def populate_rocrate(datatype: str, ome: OME, filepath: str,
                     path_id_dict: dict, folder):
    import importlib.util
    import mimetypes
    if (importlib.util.find_spec('rocrate')):
        from rocrate.rocrate import ROCrate
    else:
        raise ImportError("Could not import rocrate library. Make sure to "
                          "install omero-cli-transfer with the optional "
                          "[rocrate] addition")
    if datatype == "Plate" or datatype == "Screen":
        print("RO-Crate export of Plate/Screen currently unsupported")
        return
    rc = ROCrate()
    files = path_id_dict.items()
    for id, file in files:
        img = next(filter(lambda x: x.id == id, ome.images))
        format = mimetypes.MimeTypes().guess_type(file)[0]
        if not format:
            format = "image"
        rc.add_file(os.path.join(folder, file), properties={
                        "name": img.name,
                        "encodingFormat": format
                    })
    rc.write_zip(filepath)
    return


def populate_figures(ome: OME, conn: BlitzGateway, filepath: str):
    cli = CLI()
    cli.loadplugins()
    clean_img_ids = []
    for img in ome.images:
        clean_img_ids.append(img.id.split(":")[-1])
    q = conn.getQueryService()
    params = Parameters()
    results = q.projection(
            "SELECT f.id FROM FileAnnotation f"
            " WHERE f.ns='omero.web.figure.json'",
            params,
            conn.SERVICE_OPTS
            )
    figure_ids = [r[0].val for r in results]
    if figure_ids:
        parent = Path(filepath).parent
        figure_dir = parent / "figures"
        os.makedirs(figure_dir, exist_ok=True)
    for fig in figure_ids:
        filepath = figure_dir / ("Figure_" + str(fig) + ".json")
        cmd = ['download', "FileAnnotation:" + str(fig), str(filepath)]
        cli.invoke(cmd)
        f = open(filepath, 'r').read()
        has_images = False
        for img in clean_img_ids:
            searchterm = "\"imageId\": " + img
            if searchterm in f:
                has_images = True
        if has_images:
            fig_obj = conn.getObject("FileAnnotation", fig)
            contents = fig_obj.getFile().getPath().encode()
            b64 = base64.b64encode(contents)
            length = len(b64)
            fpath = os.path.join(fig_obj.getFile().getPath(),
                                 fig_obj.getFile().getName())
            binaryfile = BinaryFile(file_name=fpath,
                                    size=fig_obj.getFile().getSize(),
                                    bin_data=BinData(big_endian=True,
                                                     length=length,
                                                     value=b64
                                                     )
                                    )
            f, _ = create_file_ann_and_ref(id=fig_obj.getId(),
                                           namespace=fig_obj.getNs(),
                                           binary_file=binaryfile)
            filepath_ann, ref = create_figure_annotations(f.id)
            ome.structured_annotations.append(filepath_ann)
            f.annotation_ref.append(ref)
            ome.structured_annotations.append(f)
        else:
            os.remove(filepath)
    if not os.listdir(figure_dir):
        os.rmdir(figure_dir)
    return


def generate_columns(ome: OME, ids: dict) -> List[str]:
    columns = ["filename"]
    if [v for v in ids.values() if v.startswith("file_annotations")]:
        columns.append("data_type")
    for ann in ome.structured_annotations:
        if isinstance(ann, CommentAnnotation) and ("comment" not in columns):
            clean_id = int(ann.id.split(":")[-1])
            if clean_id > 0:
                columns.append("comment")
    anns = ome.structured_annotations
    for i in ome.images:
        for ann_ref in i.annotation_refs:
            ann = next(filter(lambda x: x.id == ann_ref.id, anns))
            if isinstance(ann, MapAnnotation):
                for v in ann.value.ms:
                    if v.k not in columns:
                        columns.append(v.k)
    return columns


def list_files(ome: OME, ids: dict, top_level: str) -> List[str]:
    files = []
    for k, v in ids.items():
        if v.startswith("file_annotations") or v.endswith("mock_folder"):
            files.append("more work")
        else:
            if top_level == "Project":
                proj_name = ome.projects[0].name
                dataset_name = ""
                for d in ome.datasets:
                    i = filter(lambda x: x.id == k, d.image_ref)
                    if any(i):
                        if d.name:
                            dataset_name = d.name
                image_name = v.split("/")[-1]
                if proj_name:
                    if (proj_name + "/" + dataset_name +
                            "/" + image_name) not in files:
                        files.append(proj_name + "/" + dataset_name +
                                     "/" + image_name)
    return files


def find_dataset(id: str, ome: OME) -> Union[str, None]:
    for d in ome.datasets:
        def lfunc(x): return x.id == id
        if any(filter(lfunc, d.image_refs)):
            return d.name
    return None


def generate_lines_and_move(img: Image, ome: OME, ids: dict, folder: str,
                            top_level: str, lines: List[List[str]],
                            columns: List[str]) -> dict:
    # Note that if an image is in multiple datasets (or a dataset in multiple
    # projects), only one copy of the data will exist!
    allfiles = [line[0] for line in lines]
    orig_path = ids[img.id]
    if orig_path.endswith("mock_folder"):
        subfolder = os.path.join(folder, orig_path.rsplit("/", 1)[0])
        allpaths = list(Path(subfolder).rglob("*.*"))
        clean_paths = []
        for path in allpaths:
            p = path.relative_to(subfolder)
            clean_paths.append(p)
    else:
        clean_paths = [Path(orig_path.rsplit("/", 1)[1])]
    ds_name = find_dataset(img.id, ome)
    if not ds_name:
        ds_name = ""
    paths = {}
    orig_parent = Path(orig_path).parent
    if top_level == 'Project':
        proj_name = ome.projects[0].name
        if not proj_name:
            proj_name = ""
        for p in clean_paths:
            dest = os.path.join(folder, proj_name, ds_name, p)
            orig = os.path.join(folder, orig_parent, p)
            paths[orig] = dest
    elif top_level == "Dataset":
        for p in clean_paths:
            dest = os.path.join(folder, ds_name, p)
            orig = os.path.join(folder, orig_parent, p)
            paths[orig] = dest
    for orig, dest in paths.items():
        cl_id = img.id.split(":")[-1]
        if dest in allfiles:
            idx = allfiles.index(dest)
            lines[idx][-1] = lines[idx][-1] + ", " + cl_id
        else:
            newline = [dest, "Image"]
            vals = get_annotation_vals(columns, img, ome)
            newline.extend(vals)
            newline.append(cl_id)
            lines.append(newline)
    # need to loop over images and then:

    # construct line with new path, annotations, image IDs

    # return files, lines
    return paths


def get_annotation_vals(cols: List[str], img: Image, ome: OME) -> List[str]:
    anns = []
    for annref in img.annotation_refs:
        a = next(filter(lambda x: x.id == annref.id,
                 ome.structured_annotations))
        anns.append(a)
    vals = []
    commented = False
    for col in cols:
        if col == "filename" or col == "data_type" \
           or col == "original_omero_ids":
            continue
        if col == "comment":
            for ann in anns:
                if isinstance(ann, CommentAnnotation) and \
                   int(ann.id.split(":")[-1]) > 0 and not commented:
                    vals.append(ann.value)
                    commented = True
            if not commented:
                vals.append(" ")
        else:
            hascol = False
            for ann in anns:
                if isinstance(ann, MapAnnotation) and \
                   int(ann.id.split(":")[-1]) > 0:
                    for v in ann.value.m:
                        if v.k == col:
                            vals.append(v.value)
                            hascol = True
            if not hascol:
                vals.append(" ")
    return vals


def get_file_ann_imgs(ann: FileAnnotation, ome: OME) -> str:
    ids = ""
    for i in ome.images:
        def lfunc(x): return x.id == ann.id
        if any(filter(lfunc, i.annotation_ref)):
            if ids:
                ids = ids + ", " + i.id.split(":")[-1]
            else:
                ids = i.id.split(":")[-1]
    if not ids:
        ids = " "
    return ids


def generate_lines_ann(ann: FileAnnotation, ome: OME, ids: dict,
                       cols: List[str]) -> List[str]:
    dest = ids[ann.id]
    newline = [dest, "File Annotation"]
    for col in cols:
        if col == "filename" or col == "data_type":
            continue
        if col != "original_omero_ids":
            newline.append(" ")
        else:
            ims = get_file_ann_imgs(ann, ome)
            newline.append(ims)

    return newline


def delete_empty_folders(root: str) -> set:

    deleted = set()

    for current_dir, subdirs, files in os.walk(root, topdown=False):
        still_has_subdirs = False
        for subdir in subdirs:
            if os.path.join(current_dir, subdir) not in deleted:
                still_has_subdirs = True
        if not any(files) and not still_has_subdirs:
            os.rmdir(current_dir)
            deleted.add(current_dir)

    return deleted


def write_lines(top_level: str, ome: OME, fp: TextIO, ids: dict,
                folder: str):
    columns = generate_columns(ome, ids)
    columns.append("original_omero_ids")
    writer = csv.writer(fp, delimiter='\t')
    writer.writerow(columns)
    lines: List[List[str]] = []
    paths = []
    for i in ome.images:
        tmppaths = generate_lines_and_move(i, ome, ids, folder,
                                           top_level, lines, columns)
        paths.append(tmppaths)
    for line in lines:
        line[0] = line[0].split(folder)[-1].lstrip("/")
        writer.writerow(line)
    for ann in ome.structured_annotations:
        if isinstance(ann, FileAnnotation):
            line = generate_lines_ann(ann, ome, ids, columns)
            writer.writerow(line)
    for p in paths:
        for orig, dest in p.items():
            parent = Path(dest).parent
            os.makedirs(parent, exist_ok=True)
            if Path(orig).exists():
                shutil.move(orig, dest)
    delete_empty_folders(folder)
    return
