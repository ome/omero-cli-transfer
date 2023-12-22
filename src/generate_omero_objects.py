# Copyright (C) 2022 The Jackson Laboratory
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

import ezomero
from ome_types import to_xml
from typing import List, Tuple, Union
from omero.model import DatasetI, IObject, PlateI, WellI, WellSampleI, ImageI
from omero.gateway import DatasetWrapper
from ome_types.model import TagAnnotation, MapAnnotation, FileAnnotation, ROI
from ome_types.model import CommentAnnotation, LongAnnotation, Annotation
from ome_types.model import Line, Point, Rectangle, Ellipse, Polygon, Shape
from ome_types.model import Polyline, Label, Project, Screen, Dataset, OME
from ome_types.model import Image, Plate, XMLAnnotation, AnnotationRef
from ome_types.model.simple_types import Marker
from omero.gateway import TagAnnotationWrapper, MapAnnotationWrapper
from omero.gateway import CommentAnnotationWrapper, LongAnnotationWrapper
from omero.gateway import FileAnnotationWrapper, OriginalFileWrapper
from omero.sys import Parameters
from omero.gateway import BlitzGateway
from omero.rtypes import rstring, RStringI, rint
from ezomero import rois
from pathlib import Path
import xml.etree.cElementTree as ETree
import os
import copy


def create_or_set_projects(pjs: List[Project], conn: BlitzGateway,
                           merge: bool) -> dict:
    pj_map = {}
    if not merge:
        pj_map = create_projects(pjs, conn)
    else:
        for pj in pjs:
            pj_id = find_project(pj, conn)
            if not pj_id:
                pj_id = ezomero.post_project(conn, pj.name, pj.description)
            pj_map[pj.id] = pj_id
    return pj_map


def create_projects(pjs: List[Project], conn: BlitzGateway) -> dict:
    pj_map = {}
    for pj in pjs:
        pj_id = ezomero.post_project(conn, pj.name, pj.description)
        pj_map[pj.id] = pj_id
    return pj_map


def find_project(pj: Project, conn: BlitzGateway) -> int:
    id = 0
    my_exp_id = conn.getUser().getId()
    for p in conn.getObjects("Project", opts={'owner': my_exp_id}):
        if p.getName() == pj.name:
            id = p.getId()
    return id


def create_or_set_screens(scrs: List[Screen], conn: BlitzGateway, merge: bool
                          ) -> dict:
    scr_map = {}
    if not merge:
        scr_map = create_screens(scrs, conn)
    else:
        for scr in scrs:
            scr_id = find_screen(scr, conn)
            if not scr_id:
                scr_id = ezomero.post_screen(conn, scr.name, scr.description)
            scr_map[scr.id] = scr_id
    return scr_map


def create_screens(scrs: List[Screen], conn: BlitzGateway) -> dict:
    scr_map = {}
    for scr in scrs:
        scr_id = ezomero.post_screen(conn, scr.name, scr.description)
        scr_map[scr.id] = scr_id
    return scr_map


def find_screen(sc: Screen, conn: BlitzGateway) -> int:
    id = 0
    my_exp_id = conn.getUser().getId()
    for s in conn.getObjects("Screen", opts={'owner': my_exp_id}):
        if s.getName() == sc.name:
            id = s.getId()
    return id


def create_or_set_datasets(dss: List[Dataset], pjs: List[Project],
                           conn: BlitzGateway, merge: bool) -> dict:
    ds_map = {}
    if not merge:
        ds_map = create_datasets(dss, conn)
    else:
        for ds in dss:
            ds_id = find_dataset(ds, pjs, conn)
            if not ds_id:
                dataset = DatasetWrapper(conn, DatasetI())
                dataset.setName(ds.name)
                if ds.description is not None:
                    dataset.setDescription(ds.description)
                dataset.save()
                ds_id = dataset.getId()
            ds_map[ds.id] = ds_id
    return ds_map


def create_datasets(dss: List[Dataset], conn: BlitzGateway) -> dict:
    """
    Currently doing it the non-ezomero way because ezomero always
    puts "orphan" Datasets in the user's default group
    """
    ds_map = {}
    for ds in dss:
        dataset = DatasetWrapper(conn, DatasetI())
        dataset.setName(ds.name)
        if ds.description is not None:
            dataset.setDescription(ds.description)
        dataset.save()
        ds_id = dataset.getId()
        ds_map[ds.id] = ds_id
    return ds_map


def find_dataset(ds: Dataset, pjs: List[Project], conn: BlitzGateway) -> int:
    id = 0
    my_exp_id = conn.getUser().getId()
    orphan = True
    for pj in pjs:
        for dsref in pj.dataset_refs:
            if dsref.id == ds.id:
                orphan = False
    if not orphan:
        for pj in pjs:
            for p in conn.getObjects("Project", opts={'owner': my_exp_id}):
                if p.getName() == pj.name:
                    for dsref in pj.dataset_refs:
                        if dsref.id == ds.id:
                            for ds_rem in p.listChildren():
                                if ds.name == ds_rem.getName():
                                    id = ds_rem.getId()
    else:
        for d in conn.getObjects("Dataset", opts={'owner': my_exp_id,
                                                  'orphaned': True}):
            if d.getName() == ds.name:
                id = d.getId()
    return id


def create_annotations(ans: List[Annotation], conn: BlitzGateway, hash: str,
                       folder: str, figure: bool, img_map: dict,
                       metadata: List[str]) -> dict:
    ann_map = {}
    for an in ans:
        if isinstance(an, TagAnnotation):
            tag_ann = TagAnnotationWrapper(conn)
            tag_ann.setValue(an.value)
            tag_ann.setDescription(an.description)
            tag_ann.save()
            ann_map[an.id] = tag_ann.getId()
        elif isinstance(an, MapAnnotation):
            map_ann = MapAnnotationWrapper(conn)
            namespace = an.namespace
            map_ann.setNs(namespace)
            key_value_data = []
            for v in an.value.ms:
                key_value_data.append([v.k, v.value])
            map_ann.setValue(key_value_data)
            map_ann.save()
            ann_map[an.id] = map_ann.getId()
        elif isinstance(an, CommentAnnotation):
            comm_ann = CommentAnnotationWrapper(conn)
            comm_ann.setValue(an.value)
            comm_ann.setDescription(an.description)
            comm_ann.save()
            ann_map[an.id] = comm_ann.getId()
        elif isinstance(an, LongAnnotation):
            comm_ann = LongAnnotationWrapper(conn)
            comm_ann.setValue(an.value)
            comm_ann.setDescription(an.description)
            comm_ann.setNs(an.namespace)
            comm_ann.save()
            ann_map[an.id] = comm_ann.getId()
        elif isinstance(an, FileAnnotation):
            if an.namespace == "omero.web.figure.json":
                if not figure:
                    continue
                else:
                    update_figure_refs(an, ans, img_map, folder)
            original_file = create_original_file(an, ans, conn, folder)
            file_ann = FileAnnotationWrapper(conn)
            file_ann.setDescription(an.description)
            file_ann.setNs(an.namespace)
            file_ann.setFile(original_file)
            file_ann.save()
            ann_map[an.id] = file_ann.getId()
        elif isinstance(an, XMLAnnotation):
            # pass if path, use if provenance metadata
            tree = ETree.fromstring(to_xml(an.value,
                                           canonicalize=True))
            is_metadata = False
            for el in tree:
                if el.tag.rpartition('}')[2] == "CLITransferMetadata":
                    is_metadata = True
            if is_metadata:
                map_ann = MapAnnotationWrapper(conn)
                namespace = an.namespace
                map_ann.setNs(namespace)
                key_value_data = []
                if not metadata:
                    key_value_data.append(['empty_metadata', "True"])
                else:
                    key_value_data = parse_xml_metadata(an, metadata, hash)
                map_ann.setValue(key_value_data)
                map_ann.save()
                ann_map[an.id] = map_ann.getId()
    return ann_map


def parse_xml_metadata(ann: XMLAnnotation,
                       metadata: List[str],
                       hash: str) -> List[List[str]]:
    kv_data = []
    tree = ETree.fromstring(to_xml(ann.value, canonicalize=True))
    for el in tree:
        if el.tag.rpartition('}')[2] == "CLITransferMetadata":
            for el2 in el:
                item = el2.tag.rpartition('}')[2]
                val = el2.text
                if item == "md5" and "md5" in metadata:
                    kv_data.append(['md5', hash])
                if item == "origin_image_id" and "img_id" in metadata:
                    kv_data.append([item, val])
                if item == "origin_plate_id" and "plate_id" in metadata:
                    kv_data.append([item, val])
                if item == "packing_timestamp" and "timestamp" in metadata:
                    kv_data.append([item, val])
                if item == "software" and "software" in metadata:
                    kv_data.append([item, val])
                if item == "version" and "version" in metadata:
                    kv_data.append([item, val])
                if item == "origin_hostname" and "hostname" in metadata:
                    kv_data.append([item, val])
                if item == "original_user" and "orig_user" in metadata:
                    kv_data.append([item, val])
                if item == "original_group" and "orig_group" in metadata:
                    kv_data.append([item, val])
                if item == "database_id" and "db_id" in metadata:
                    kv_data.append([item, val])
    return kv_data


def get_server_path(anrefs: List[AnnotationRef],
                    ans: List[Annotation]) -> Union[str, None]:
    fpath = None
    xml_ids = []
    for an in anrefs:
        for an_loop in ans:
            if an.id == an_loop.id:
                if isinstance(an_loop, XMLAnnotation):
                    xml_ids.append(an_loop.id)
                else:
                    continue
    for an_loop in ans:
        if an_loop.id in xml_ids:
            if not fpath:
                tree = ETree.fromstring(to_xml(an_loop.value,
                                               canonicalize=True))
                for el in tree:
                    if el.tag.rpartition('}')[2] == "CLITransferServerPath":
                        for el2 in el:
                            if el2.tag.rpartition('}')[2] == "Path":
                                fpath = el2.text
    return fpath


def update_figure_refs(ann: FileAnnotation, ans: List[Annotation],
                       img_map: dict, folder: str):
    curr_folder = str(Path('.').resolve())
    fpath = get_server_path(ann.annotation_refs, ans)
    if fpath:
        dest_path = str(os.path.join(curr_folder, folder,  '.', fpath))
        with open(dest_path, 'r') as file:
            filedata = file.read()
        for src_id, dest_id in img_map.items():
            clean_id = int(src_id.split(":")[-1])
            src_str = f"\"imageId\": {clean_id}"
            dest_str = f"\"imageId\": {dest_id}"
            filedata = filedata.replace(src_str, dest_str)
        with open(dest_path, 'w') as file:
            file.write(filedata)
    return


def create_original_file(ann: FileAnnotation, ans: List[Annotation],
                         conn: BlitzGateway, folder: str
                         ) -> OriginalFileWrapper:
    curr_folder = str(Path('.').resolve())
    fpath = get_server_path(ann.annotation_refs, ans)
    dest_path = str(os.path.join(curr_folder, folder,  '.', fpath))
    ofile = conn.createOriginalFileFromLocalFile(dest_path)
    return ofile


def create_plate_map(ome: OME, img_map: dict, conn: BlitzGateway
                     ) -> Tuple[dict, OME]:
    newome = copy.deepcopy(ome)
    plate_map = {}
    map_ref_ids = []
    for plate in ome.plates:
        ann_ids = [i.id for i in plate.annotation_refs]
        for ann in ome.structured_annotations:
            if (ann.id in ann_ids and
                    isinstance(ann, XMLAnnotation)):
                tree = ETree.fromstring(to_xml(ann.value,
                                               canonicalize=True))
                is_metadata = False
                for el in tree:
                    if el.tag.rpartition('}')[2] == "CLITransferMetadata":
                        is_metadata = True
                if not is_metadata:
                    newome.structured_annotations.remove(ann)
                    map_ref_ids.append(ann.id)
                    file_path = get_server_path(plate.annotation_refs,
                                                ome.structured_annotations)
                    annref = next(filter(lambda x: x.id == ann.id,
                                         plate.annotation_refs))
                    newplate = next(filter(lambda x: x.id == plate.id,
                                           newome.plates))
                    newplate.annotation_refs.remove(annref)
        q = conn.getQueryService()
        params = Parameters()
        if not file_path:
            raise ValueError(f"Plate ID {plate.id} does not have a \
                             XMLAnnotation with a file path!")
        path_query = str(file_path).strip('/')
        if path_query.endswith('mock_folder'):
            path_query = path_query.rstrip("mock_folder")
        params.map = {"cpath": rstring('%%%s%%' % path_query)}
        results = q.projection(
            "SELECT p.id FROM Plate p"
            " JOIN p.plateAcquisitions a"
            " JOIN a.wellSample w"
            " JOIN w.image i"
            " JOIN i.fileset fs"
            " JOIN fs.usedFiles u"
            " WHERE u.clientPath LIKE :cpath",
            params,
            conn.SERVICE_OPTS
            )
        all_plate_ids = list(set(sorted([r[0].val for r in results])))
        plate_ids = []
        for pl_id in all_plate_ids:
            anns = ezomero.get_map_annotation_ids(conn, "Plate", pl_id)
            if not anns:
                plate_ids.append(pl_id)
            else:
                is_annotated = False
                for ann in anns:
                    ann_content = conn.getObject("MapAnnotation", ann)
                    if ann_content.getNs() == \
                            'openmicroscopy.org/cli/transfer':
                        is_annotated = True
                if not is_annotated:
                    plate_ids.append(pl_id)
        if plate_ids:
            # plate was imported as plate
            plate_id = plate_ids[0]
        else:
            # plate was imported as images
            plate_id = create_plate_from_images(plate, img_map, conn)
        plate_map[plate.id] = plate_id
    for p in newome.plates:
        for ref in p.annotation_refs:
            if ref.id in map_ref_ids:
                p.annotation_refs.remove(ref)
    return plate_map, newome


def create_plate_from_images(plate: Plate, img_map: dict, conn: BlitzGateway
                             ) -> int:
    plateobj = PlateI()
    plateobj.name = RStringI(plate.name)
    plateobj = conn.getUpdateService().saveAndReturnObject(plateobj)
    plate_id = plateobj.getId().getValue()
    for well in plate.wells:
        img_ids = []
        for ws in well.well_samples:
            if ws.image_ref:
                for imgref in ws.image_ref:
                    img_ids.append(img_map[imgref[-1]])
        add_image_to_plate(img_ids, plate_id, well.column,
                           well.row, conn)
    return plate_id


def add_image_to_plate(image_ids: List[int], plate_id: int, column: int,
                       row: int, conn: BlitzGateway) -> bool:
    """
    Add the Images to a Plate, creating a new well at the specified column and
    row
    NB - This will fail if there is already a well at that point
    """
    update_service = conn.getUpdateService()

    well = WellI()
    well.plate = PlateI(plate_id, False)
    well.column = rint(column)
    well.row = rint(row)

    try:
        for image_id in image_ids:
            image = conn.getObject("Image", image_id)
            ws = WellSampleI()
            ws.image = ImageI(image.id, False)
            ws.well = well
            well.addWellSample(ws)
        update_service.saveObject(well)
    except Exception:
        return False
    return True


def create_shapes(roi: ROI) -> List[Shape]:
    shapes = []
    for shape in roi.union:
        if shape.fill_color:
            fc = shape.fill_color.as_rgb_tuple()
            if len(fc) == 3:
                fill_color = fc + (255,)
            else:
                alpha = fc[3] * 255
                fill_color = fc[0:3] + (int(alpha),)
        else:
            fill_color = (0, 0, 0, 0)
        if shape.stroke_color:
            sc = shape.stroke_color.as_rgb_tuple()
            if len(sc) == 3:
                stroke_color = sc + (255,)
            else:
                stroke_color = sc
        else:
            stroke_color = (255, 255, 255, 255)
        if shape.stroke_width:
            stroke_width = int(shape.stroke_width)
        else:
            stroke_width = 1
        if isinstance(shape, Point):
            sh = rois.Point(shape.x, shape.y, z=shape.the_z, c=shape.the_c,
                            t=shape.the_t, label=shape.text,
                            fill_color=fill_color, stroke_color=stroke_color,
                            stroke_width=stroke_width)
        elif isinstance(shape, Line):
            if shape.marker_start == Marker.ARROW:
                mk_start = "Arrow"
            else:
                mk_start = str(shape.marker_start)
            if shape.marker_end == Marker.ARROW:
                mk_end = "Arrow"
            else:
                mk_end = str(shape.marker_end)
            sh = rois.Line(shape.x1, shape.y1, shape.x2, shape.y2,
                           z=shape.the_z, c=shape.the_c, t=shape.the_t,
                           label=shape.text, markerStart=mk_start,
                           markerEnd=mk_end)
        elif isinstance(shape, Rectangle):
            sh = rois.Rectangle(shape.x, shape.y, shape.width, shape.height,
                                z=shape.the_z, c=shape.the_c, t=shape.the_t,
                                label=shape.text)
        elif isinstance(shape, Ellipse):
            sh = rois.Ellipse(shape.x, shape.y, shape.radius_x, shape.radius_y,
                              z=shape.the_z, c=shape.the_c, t=shape.the_t,
                              label=shape.text)
        elif isinstance(shape, Polygon):
            points = []
            for pt in shape.points.split(" "):
                # points sometimes come with a comma at the end...
                pt = pt.rstrip(",")
                points.append(tuple(float(x) for x in pt.split(",")))
            sh = rois.Polygon(points, z=shape.the_z, c=shape.the_c,
                              t=shape.the_t, label=shape.text)
        elif isinstance(shape, Polyline):
            points = []
            for pt in shape.points.split(" "):
                # points sometimes come with a comma at the end...
                pt = pt.rstrip(",")
                points.append(tuple(float(x) for x in pt.split(",")))
            sh = rois.Polyline(points, z=shape.the_z, c=shape.the_c,
                               t=shape.the_t, label=shape.text)
        elif isinstance(shape, Label):
            sh = rois.Label(shape.x, shape.y, z=shape.the_z, c=shape.the_c,
                            t=shape.the_t, label=shape.text,
                            fontSize=shape.font_size)
        else:
            continue
        shapes.append(sh)
    return shapes


def _int_to_rgba(omero_val: int) -> Tuple[int, int, int, int]:
    """ Helper function returning the color as an Integer in RGBA encoding """
    if omero_val < 0:
        omero_val = omero_val + (2**32)
    r = omero_val >> 24
    g = omero_val - (r << 24) >> 16
    b = omero_val - (r << 24) - (g << 16) >> 8
    a = omero_val - (r << 24) - (g << 16) - (b << 8)
    # a = a / 256.0
    return (r, g, b, a)


def create_rois(rois: List[ROI], imgs: List[Image], img_map: dict,
                conn: BlitzGateway):
    for img in imgs:
        for roiref in img.roi_refs:
            roi = next(filter(lambda x: x.id == roiref.id, rois))
            shapes = create_shapes(roi)
            img_id_dest = img_map[img.id]
            ezomero.post_roi(conn, img_id_dest, shapes, name=roi.name,
                             description=roi.description)
    return


def link_datasets(ome: OME, proj_map: dict, ds_map: dict, conn: BlitzGateway):
    for proj in ome.projects:
        proj_id = proj_map[proj.id]
        proj_obj = conn.getObject("Project", proj_id)
        existing_ds = []
        for dataset in proj_obj.listChildren():
            existing_ds.append(dataset.getId())
        ds_ids = []
        for ds in proj.dataset_refs:
            ds_id = ds_map[ds.id]
            if ds_id not in existing_ds:
                ds_ids.append(ds_id)
        ezomero.link_datasets_to_project(conn, ds_ids, proj_id)
    return


def link_plates(ome: OME, screen_map: dict, plate_map: dict,
                conn: BlitzGateway):
    for screen in ome.screens:
        screen_id = screen_map[screen.id]
        scr_obj = conn.getObject("Screen", screen_id)
        existing_pl = []
        for pl in scr_obj.listChildren():
            existing_pl.append(pl.getId())
        pl_ids = []
        for pl in screen.plate_refs:
            pl_id = plate_map[pl.id]
            if pl_id not in existing_pl:
                pl_ids.append(pl_id)
        ezomero.link_plates_to_screen(conn, pl_ids, screen_id)
    return


def link_images(ome: OME, ds_map: dict, img_map: dict, conn: BlitzGateway):
    for ds in ome.datasets:
        ds_id = ds_map[ds.id]
        img_ids = []
        for img in ds.image_refs:
            try:
                img_id = img_map[img.id]
                img_ids.append(img_id)
            except KeyError:
                continue
        ezomero.link_images_to_dataset(conn, img_ids, ds_id)
    return


def link_annotations(ome: OME, proj_map: dict, ds_map: dict, img_map: dict,
                     ann_map: dict, scr_map: dict, pl_map: dict,
                     conn: BlitzGateway):
    for proj in ome.projects:
        proj_id = proj_map[proj.id]
        proj_obj = conn.getObject("Project", proj_id)
        anns = ome.structured_annotations
        for annref in proj.annotation_refs:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(proj_obj, ann, ann_map, conn)
    for ds in ome.datasets:
        ds_id = ds_map[ds.id]
        ds_obj = conn.getObject("Dataset", ds_id)
        anns = ome.structured_annotations
        for annref in ds.annotation_refs:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(ds_obj, ann, ann_map, conn)
    for img in ome.images:
        try:
            img_id = img_map[img.id]
            img_obj = conn.getObject("Image", img_id)
            anns = ome.structured_annotations
            for annref in img.annotation_refs:
                ann = next(filter(lambda x: x.id == annref.id, anns))
                link_one_annotation(img_obj, ann, ann_map, conn)
        except KeyError:
            continue
    for scr in ome.screens:
        scr_id = scr_map[scr.id]
        scr_obj = conn.getObject("Screen", scr_id)
        anns = ome.structured_annotations
        for annref in scr.annotation_refs:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(scr_obj, ann, ann_map, conn)
    for pl in ome.plates:
        pl_id = pl_map[pl.id]
        pl_obj = conn.getObject("Plate", pl_id)
        anns = ome.structured_annotations
        for annref in pl.annotation_refs:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(pl_obj, ann, ann_map, conn)
        anns = ome.structured_annotations
        for well in pl.wells:
            if len(well.annotation_refs) > 0:
                row, col = well.row, well.column
                well_id = ezomero.get_well_id(conn, pl_id, row, col)
                well_obj = conn.getObject("Well", well_id)
                for annref in well.annotation_refs:
                    ann = next(filter(lambda x: x.id == annref.id, anns))
                    link_one_annotation(well_obj, ann, ann_map, conn)
    return


def link_one_annotation(obj: IObject, ann: Annotation, ann_map: dict,
                        conn: BlitzGateway):
    ann_id = ann_map[ann.id]
    if isinstance(ann, TagAnnotation):
        ann_obj = conn.getObject("TagAnnotation", ann_id)
    elif isinstance(ann, MapAnnotation):
        ann_obj = conn.getObject("MapAnnotation", ann_id)
    elif isinstance(ann, CommentAnnotation):
        ann_obj = conn.getObject("CommentAnnotation", ann_id)
    elif isinstance(ann, LongAnnotation):
        ann_obj = conn.getObject("LongAnnotation", ann_id)
    elif isinstance(ann, FileAnnotation):
        ann_obj = conn.getObject("FileAnnotation", ann_id)
    elif isinstance(ann, XMLAnnotation):
        ann_obj = conn.getObject("MapAnnotation", ann_id)
    else:
        ann_obj = None
    if ann_obj:
        obj.linkAnnotation(ann_obj)


def rename_images(imgs: List[Image], img_map: dict, conn: BlitzGateway):
    for img in imgs:
        try:
            img_id = img_map[img.id]
            im_obj = conn.getObject("Image", img_id)
            im_obj.setName(img.name)
            im_obj.save()
        except KeyError:
            print(f"Image corresponding to {img.id} not found. Skipping.")
    return


def rename_plates(pls: List[Plate], pl_map: dict, conn: BlitzGateway):
    for pl in pls:
        try:
            pl_id = pl_map[pl.id]
            pl_obj = conn.getObject("Plate", pl_id)
            pl_obj.setName(pl.name)
            pl_obj.save()
        except KeyError:
            print(f"Plate corresponding to {pl.id} not found. Skipping.")
    return


def populate_omero(ome: OME, img_map: dict, conn: BlitzGateway, hash: str,
                   folder: str, metadata: List[str], merge: bool,
                   figure: bool):
    plate_map, ome = create_plate_map(ome, img_map, conn)
    rename_images(ome.images, img_map, conn)
    rename_plates(ome.plates, plate_map, conn)
    proj_map = create_or_set_projects(ome.projects, conn, merge)
    ds_map = create_or_set_datasets(ome.datasets, ome.projects, conn, merge)
    screen_map = create_or_set_screens(ome.screens, conn, merge)
    ann_map = create_annotations(ome.structured_annotations, conn,
                                 hash, folder, figure, img_map, metadata)
    create_rois(ome.rois, ome.images, img_map, conn)
    link_plates(ome, screen_map, plate_map, conn)
    link_datasets(ome, proj_map, ds_map, conn)
    link_images(ome, ds_map, img_map, conn)
    link_annotations(ome, proj_map, ds_map, img_map, ann_map,
                     screen_map, plate_map, conn)
    return
