import ezomero
from typing import List, Tuple
from omero.model import DatasetI, IObject
from omero.gateway import DatasetWrapper
from ome_types.model import TagAnnotation, MapAnnotation, FileAnnotation, ROI
from ome_types.model import CommentAnnotation, LongAnnotation, Annotation
from ome_types.model import Line, Point, Rectangle, Ellipse, Polygon, Shape
from ome_types.model import Polyline, Label, Project, Screen, Dataset, OME
from ome_types.model import Image
from ome_types.model.simple_types import Marker
from omero.gateway import TagAnnotationWrapper, MapAnnotationWrapper
from omero.gateway import CommentAnnotationWrapper, LongAnnotationWrapper
from omero.gateway import FileAnnotationWrapper, OriginalFileWrapper
from omero.sys import Parameters
from omero.gateway import BlitzGateway
from omero.rtypes import rstring
from ezomero import rois
from pathlib import Path
import os
import copy


def create_projects(pjs: List[Project], conn: BlitzGateway) -> dict:
    pj_map = {}
    for pj in pjs:
        pj_id = ezomero.post_project(conn, pj.name, pj.description)
        pj_map[pj.id] = pj_id
    return pj_map


def create_screens(scrs: List[Screen], conn: BlitzGateway) -> dict:
    scr_map = {}
    for scr in scrs:
        scr_id = ezomero.post_screen(conn, scr.name, scr.description)
        scr_map[scr.id] = scr_id
    return scr_map


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


def create_annotations(ans: List[Annotation], conn: BlitzGateway, hash: str,
                       folder: str, metadata: List[str]) -> dict:
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
            for v in an.value.m:
                if int(an.id.split(":")[-1]) < 0:
                    if not metadata:
                        key_value_data.append(['empty_metadata', "True"])
                        break
                    if v.k == "md5" and "md5" in metadata:
                        key_value_data.append(['zip_file_md5', hash])
                    if v.k == "origin_image_id" and "img_id" in metadata:
                        key_value_data.append([v.k, v.value])
                    if v.k == "packing_timestamp" and "timestamp" in metadata:
                        key_value_data.append([v.k, v.value])
                    if v.k == "software" and "software" in metadata:
                        key_value_data.append([v.k, v.value])
                    if v.k == "version" and "version" in metadata:
                        key_value_data.append([v.k, v.value])
                    if v.k == "origin_hostname" and "hostname" in metadata:
                        key_value_data.append([v.k, v.value])
                    if v.k == "original_user" and "orig_user" in metadata:
                        key_value_data.append([v.k, v.value])
                    if v.k == "original_group" and "orig_group" in metadata:
                        key_value_data.append([v.k, v.value])
                    if v.k == "database_id" and "db_id" in metadata:
                        key_value_data.append([v.k, v.value])
                else:
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
            original_file = create_original_file(an, ans, conn, folder)
            file_ann = FileAnnotationWrapper(conn)
            file_ann.setDescription(an.description)
            file_ann.setNs(an.namespace)
            file_ann.setFile(original_file)
            file_ann.save()
            ann_map[an.id] = file_ann.getId()
    return ann_map


def create_original_file(ann: FileAnnotation, ans: List[Annotation],
                         conn: BlitzGateway, folder: str
                         ) -> OriginalFileWrapper:
    curr_folder = str(Path('.').resolve())
    for an in ann.annotation_ref:
        clean_id = int(an.id.split(":")[-1])
        if clean_id < 0:
            cmnt_id = an.id
    for an_loop in ans:
        if an_loop.id == cmnt_id and isinstance(an_loop, CommentAnnotation):
            fpath = str(an_loop.value)
    dest_path = str(os.path.join(curr_folder, folder,  '.', fpath))
    ofile = conn.createOriginalFileFromLocalFile(dest_path)
    return ofile


def create_plate_map(ome: OME, conn: BlitzGateway) -> Tuple[dict, OME]:

    newome = copy.deepcopy(ome)
    plate_map = {}
    map_ref_ids = []
    for plate in ome.plates:
        ann_ids = [i.id for i in plate.annotation_ref]
        for ann in ome.structured_annotations:
            if (ann.id in ann_ids and
                    type(ann) == CommentAnnotation and
                    int(ann.id.split(":")[-1]) < 0):
                newome.structured_annotations.remove(ann)
                map_ref_ids.append(ann.id)
                file_path = ann.value
        q = conn.getQueryService()
        params = Parameters()
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
        plate_id = results[0][0].val
        plate_map[plate.id] = plate_id
    for p in newome.plates:
        for ref in p.annotation_ref:
            if ref.id in map_ref_ids:
                p.annotation_ref.remove(ref)
    return plate_map, newome


def create_shapes(roi: ROI) -> List[Shape]:
    shapes = []
    for shape in roi.union:
        if isinstance(shape, Point):
            sh = rois.Point(shape.x, shape.y, z=shape.the_z, c=shape.the_c,
                            t=shape.the_t, label=shape.text)
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


# def _int_to_rgba(omero_val: int) -> Tuple[int, int, int, int]:
#    """ Helper function returning the color as an Integer in RGBA encoding """
#     if omero_val < 0:
#         omero_val = omero_val + (2**32)
#     r = omero_val >> 24
#     g = omero_val - (r << 24) >> 16
#     b = omero_val - (r << 24) - (g << 16) >> 8
#     a = omero_val - (r << 24) - (g << 16) - (b << 8)
#     # a = a / 256.0
#     return (r, g, b, a)


def create_rois(rois: List[ROI], imgs: List[Image], img_map: dict,
                conn: BlitzGateway):
    for img in imgs:
        for roiref in img.roi_ref:
            roi = next(filter(lambda x: x.id == roiref.id, rois))
            print(roi)
            shapes = create_shapes(roi)
            print(roi.union[0].fill_color)
            if roi.union[0].fill_color:
                fc = roi.union[0].fill_color.as_rgb_tuple()
                if len(fc) == 3:
                    fill_color = fc + (0,)
                else:
                    fill_color = fc
            if roi.union[0].stroke_color:
                sc = roi.union[0].stroke_color.as_rgb_tuple()
                if len(sc) == 3:
                    stroke_color = sc + (0,)
                else:
                    stroke_color = sc
            img_id_dest = img_map[img.id]
            # using colors for the first shape
            # fill_color = _int_to_rgba(int(str(roi.union[0].fill_color)))
            # stroke_color = _int_to_rgba(int(str(roi.union[0].stroke_color)))
            ezomero.post_roi(conn, img_id_dest, shapes, name=roi.name,
                             description=roi.description,
                             fill_color=fill_color, stroke_color=stroke_color)
    return


def link_datasets(ome: OME, proj_map: dict, ds_map: dict, conn: BlitzGateway):
    for proj in ome.projects:
        proj_id = proj_map[proj.id]
        ds_ids = []
        for ds in proj.dataset_ref:
            ds_id = ds_map[ds.id]
            ds_ids.append(ds_id)
        ezomero.link_datasets_to_project(conn, ds_ids, proj_id)
    return


def link_plates(ome: OME, screen_map: dict, plate_map: dict,
                conn: BlitzGateway):
    for screen in ome.screens:
        screen_id = screen_map[screen.id]
        pl_ids = []
        for pl in screen.plate_ref:
            pl_id = plate_map[pl.id]
            pl_ids.append(pl_id)
        ezomero.link_plates_to_screen(conn, pl_ids, screen_id)
    return


def link_images(ome: OME, ds_map: dict, img_map: dict, conn: BlitzGateway):
    for ds in ome.datasets:
        ds_id = ds_map[ds.id]
        img_ids = []
        for img in ds.image_ref:
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
        for annref in proj.annotation_ref:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(proj_obj, ann, ann_map, conn)
    for ds in ome.datasets:
        ds_id = ds_map[ds.id]
        ds_obj = conn.getObject("Dataset", ds_id)
        anns = ome.structured_annotations
        for annref in ds.annotation_ref:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(ds_obj, ann, ann_map, conn)
    for img in ome.images:
        try:
            img_id = img_map[img.id]
            img_obj = conn.getObject("Image", img_id)
            anns = ome.structured_annotations
            for annref in img.annotation_ref:
                ann = next(filter(lambda x: x.id == annref.id, anns))
                link_one_annotation(img_obj, ann, ann_map, conn)
        except KeyError:
            continue
    for scr in ome.screens:
        scr_id = scr_map[scr.id]
        scr_obj = conn.getObject("Screen", scr_id)
        anns = ome.structured_annotations
        for annref in scr.annotation_ref:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(scr_obj, ann, ann_map, conn)
    for pl in ome.plates:
        pl_id = pl_map[pl.id]
        pl_obj = conn.getObject("Plate", pl_id)
        anns = ome.structured_annotations
        for annref in pl.annotation_ref:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(pl_obj, ann, ann_map, conn)
        anns = ome.structured_annotations
        for well in pl.wells:
            if len(well.annotation_ref) > 0:
                row, col = well.row, well.column
                well_id = ezomero.get_well_id(conn, pl_id, row, col)
                well_obj = conn.getObject("Well", well_id)
                for annref in well.annotation_ref:
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


def populate_omero(ome: OME, img_map: dict, conn: BlitzGateway, hash: str,
                   folder: str, metadata: List[str]):
    rename_images(ome.images, img_map, conn)
    proj_map = create_projects(ome.projects, conn)
    ds_map = create_datasets(ome.datasets, conn)
    screen_map = create_screens(ome.screens, conn)
    plate_map, ome = create_plate_map(ome, conn)
    ann_map = create_annotations(ome.structured_annotations, conn,
                                 hash, folder, metadata)
    create_rois(ome.rois, ome.images, img_map, conn)
    link_plates(ome, screen_map, plate_map, conn)
    link_datasets(ome, proj_map, ds_map, conn)
    link_images(ome, ds_map, img_map, conn)
    link_annotations(ome, proj_map, ds_map, img_map, ann_map,
                     screen_map, plate_map, conn)
    return
