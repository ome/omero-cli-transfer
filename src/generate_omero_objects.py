import ezomero
from omero.model import DatasetI
from omero.gateway import DatasetWrapper
from ome_types.model import TagAnnotation, MapAnnotation, FileAnnotation
from ome_types.model import CommentAnnotation, LongAnnotation
from ome_types.model import Line, Point, Rectangle, Ellipse, Polygon
from ome_types.model import Polyline, Label
from ome_types.model.simple_types import Marker
from omero.gateway import TagAnnotationWrapper, MapAnnotationWrapper
from omero.gateway import CommentAnnotationWrapper, LongAnnotationWrapper
from omero.gateway import FileAnnotationWrapper
from omero.sys import Parameters
from omero.rtypes import rstring
from ezomero import rois
from pathlib import Path
import os
import copy


def create_projects(pjs, conn):
    pj_map = {}
    for pj in pjs:
        pj_id = ezomero.post_project(conn, pj.name, pj.description)
        pj_map[pj.id] = pj_id
    return pj_map


def create_screens(scrs, conn):
    scr_map = {}
    for scr in scrs:
        scr_id = ezomero.post_screen(conn, scr.name, scr.description)
        scr_map[scr.id] = scr_id
    return scr_map


def create_datasets(dss, conn):
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


def create_annotations(ans, conn, hash, folder):
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
                key_value_data.append([v.k, v.value])
            if int(an.id.split(":")[-1]) < 0:
                key_value_data.append(['zip_file_md5', hash])
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


def create_original_file(ann, ans, conn, folder):
    print(ann)
    curr_folder = str(Path('.').resolve())
    for an in ann.annotation_ref:
        clean_id = int(an.id.split(":")[-1])
        if clean_id < 0:
            cmnt_id = an.id
    for an in ans:
        if an.id == cmnt_id:
            fpath = an.value
    dest_path = str(os.path.join(curr_folder, folder,  '.', fpath))
    ofile = conn.createOriginalFileFromLocalFile(dest_path)
    return ofile


def create_plate_map(ome, conn):
    """Get the Ids of imported images.
    Note that this will not find images if they have not been imported.

    Returns
    -------
    image_ids : list of ints
        Ids of images imported from the specified client path, which
        itself is derived from ``file_path``.
    """
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


def create_shapes(roi):
    shapes = []
    for shape in roi.union:
        if isinstance(shape, Point):
            sh = rois.Point(shape.x, shape.y, z=shape.the_z, c=shape.the_c,
                            t=shape.the_t, label=shape.text)
        elif isinstance(shape, Line):
            if shape.marker_start == Marker.ARROW:
                mk_start = "Arrow"
            else:
                mk_start = shape.marker_start
            if shape.marker_end == Marker.ARROW:
                mk_end = "Arrow"
            else:
                mk_end = shape.marker_end
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


def _int_to_rgba(omero_val):
    """ Helper function returning the color as an Integer in RGBA encoding """
    if omero_val < 0:
        omero_val = omero_val + (2**32)
    r = omero_val >> 24
    g = omero_val - (r << 24) >> 16
    b = omero_val - (r << 24) - (g << 16) >> 8
    a = omero_val - (r << 24) - (g << 16) - (b << 8)
    # a = a / 256.0
    return (r, g, b, a)


def create_rois(rois, imgs, img_map, conn):
    for img in imgs:
        for roiref in img.roi_ref:
            roi = next(filter(lambda x: x.id == roiref.id, rois))
            shapes = create_shapes(roi)
            img_id_dest = img_map[img.id]
            # using colors for the first shape
            fill_color = _int_to_rgba(int(roi.union[0].fill_color))
            stroke_color = _int_to_rgba(int(roi.union[0].stroke_color))
            ezomero.post_roi(conn, img_id_dest, shapes, name=roi.name,
                             description=roi.description,
                             fill_color=fill_color, stroke_color=stroke_color)
    return


def link_datasets(ome, proj_map, ds_map, conn):
    for proj in ome.projects:
        proj_id = proj_map[proj.id]
        ds_ids = []
        for ds in proj.dataset_ref:
            ds_id = ds_map[ds.id]
            ds_ids.append(ds_id)
        ezomero.link_datasets_to_project(conn, ds_ids, proj_id)
    return


def link_plates(ome, screen_map, plate_map, conn):
    for screen in ome.screens:
        screen_id = screen_map[screen.id]
        pl_ids = []
        for pl in screen.plate_ref:
            pl_id = plate_map[pl.id]
            pl_ids.append(pl_id)
        ezomero.link_plates_to_screen(conn, pl_ids, screen_id)
    return


def link_images(ome, ds_map, img_map, conn):
    for ds in ome.datasets:
        ds_id = ds_map[ds.id]
        img_ids = []
        for img in ds.image_ref:
            img_id = img_map[img.id]
            img_ids.append(img_id)
        ezomero.link_images_to_dataset(conn, img_ids, ds_id)
    return


def link_annotations(ome, proj_map, ds_map, img_map, ann_map,
                     scr_map, pl_map, conn):
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
        img_id = img_map[img.id]
        img_obj = conn.getObject("Image", img_id)
        anns = ome.structured_annotations
        for annref in img.annotation_ref:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            link_one_annotation(img_obj, ann, ann_map, conn)
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


def link_one_annotation(obj, ann, ann_map, conn):
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


def rename_images(imgs, img_map, conn):
    for img in imgs:
        img_id = img_map[img.id]
        im_obj = conn.getObject("Image", img_id)
        im_obj.setName(img.name)
        im_obj.save()
    return


def populate_omero(ome, img_map, conn, hash, folder):
    rename_images(ome.images, img_map, conn)
    proj_map = create_projects(ome.projects, conn)
    ds_map = create_datasets(ome.datasets, conn)
    screen_map = create_screens(ome.screens, conn)
    plate_map, ome = create_plate_map(ome, conn)
    ann_map = create_annotations(ome.structured_annotations, conn,
                                 hash, folder)
    create_rois(ome.rois, ome.images, img_map, conn)
    link_plates(ome, screen_map, plate_map, conn)
    link_datasets(ome, proj_map, ds_map, conn)
    link_images(ome, ds_map, img_map, conn)
    link_annotations(ome, proj_map, ds_map, img_map, ann_map,
                     screen_map, plate_map, conn)
    return
