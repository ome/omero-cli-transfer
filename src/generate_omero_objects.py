import ezomero
import argparse
from omero.model import DatasetI
from omero.gateway import DatasetWrapper
from ome_types import from_xml
from ome_types.model import TagAnnotation, MapAnnotation
from ome_types.model import Line, Point, Rectangle, Ellipse, Polygon, Polyline
from omero.gateway import TagAnnotationWrapper, MapAnnotationWrapper
from ezomero import rois


def create_projects(pjs, conn):
    pj_map = {}
    for pj in pjs:
        pj_id = ezomero.post_project(conn, pj.name, pj.description)
        pj_map[pj.id] = pj_id
    return pj_map


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


def create_annotations(ans, conn):
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
            map_ann.setValue(key_value_data)
            map_ann.save()
            ann_map[an.id] = map_ann.getId()
    return ann_map


def create_shapes(roi):
    shapes = []
    for shape in roi.union:
        if isinstance(shape, Point):
            sh = rois.Point(shape.x, shape.y, z=shape.the_z, c=shape.the_c,
                            t=shape.the_t, label=shape.text)
        elif isinstance(shape, Line):
            sh = rois.Line(shape.x1, shape.y1, shape.x2, shape.y2,
                           z=shape.the_z, c=shape.the_c, t=shape.the_t,
                           label=shape.text)
        elif isinstance(shape, Rectangle):
            sh = rois.Rectangle(shape.x, shape.y, shape.width, shape.height,
                                z=shape.the_z, c=shape.the_c, t=shape.the_t,
                                label=shape.text)
        elif isinstance(shape, Ellipse):
            sh = rois.Ellipse(shape.x, shape.y, shape.radius_x, shape.radius_y,
                              z=shape.the_z, c=shape.the_c, t=shape.the_t,
                              label=shape.text)
        elif isinstance(shape, Polygon) or isinstance(shape, Polyline):
            points = []
            for pt in shape.points.split(" "):
                # points sometimes come with a comma at the end...
                pt = pt.rstrip(",")
                points.append(tuple(float(x) for x in pt.split(",")))
            sh = rois.Polygon(points, z=shape.the_z, c=shape.the_c,
                              t=shape.the_t, label=shape.text)
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
    a = a / 256.0
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


def link_images(ome, ds_map, img_map, conn):
    for ds in ome.datasets:
        ds_id = ds_map[ds.id]
        img_ids = []
        for img in ds.image_ref:
            img_id = img_map[img.id]
            img_ids.append(img_id)
        ezomero.link_images_to_dataset(conn, img_ids, ds_id)
    return


def link_annotations(ome, proj_map, ds_map, img_map, ann_map, conn):
    for proj in ome.projects:
        proj_id = proj_map[proj.id]
        proj_obj = conn.getObject("Project", proj_id)
        anns = ome.structured_annotations
        for annref in proj.annotation_ref:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            ann_id = ann_map[ann.id]
            if isinstance(ann, TagAnnotation):
                ann_obj = conn.getObject("TagAnnotation", ann_id)
            elif isinstance(ann, MapAnnotation):
                ann_obj = conn.getObject("MapAnnotation", ann_id)
            else:
                continue
            proj_obj.linkAnnotation(ann_obj)
    for ds in ome.datasets:
        ds_id = ds_map[ds.id]
        ds_obj = conn.getObject("Dataset", ds_id)
        anns = ome.structured_annotations
        for annref in ds.annotation_ref:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            ann_id = ann_map[ann.id]
            if isinstance(ann, TagAnnotation):
                ann_obj = conn.getObject("TagAnnotation", ann_id)
            elif isinstance(ann, MapAnnotation):
                ann_obj = conn.getObject("MapAnnotation", ann_id)
            else:
                continue
            ds_obj.linkAnnotation(ann_obj)
    for img in ome.images:
        img_id = img_map[img.id]
        img_obj = conn.getObject("Image", img_id)
        anns = ome.structured_annotations
        for annref in img.annotation_ref:
            ann = next(filter(lambda x: x.id == annref.id, anns))
            ann_id = ann_map[ann.id]
            if isinstance(ann, TagAnnotation):
                ann_obj = conn.getObject("TagAnnotation", ann_id)
            elif isinstance(ann, MapAnnotation):
                ann_obj = conn.getObject("MapAnnotation", ann_id)
            else:
                continue
            img_obj.linkAnnotation(ann_obj)
    return


def populate_omero(ome, img_map, conn):
    proj_map = create_projects(ome.projects, conn)
    print(proj_map)
    ds_map = create_datasets(ome.datasets, conn)
    print(ds_map)
    ann_map = create_annotations(ome.structured_annotations, conn)
    print(ann_map)
    create_rois(ome.rois, ome.images, img_map, conn)
    link_datasets(ome, proj_map, ds_map, conn)
    link_images(ome, ds_map, img_map, conn)
    link_annotations(ome, proj_map, ds_map, img_map, ann_map, conn)
    conn.close()
    return


if __name__ == "__main__":
    conn = ezomero.connect('root', 'omero', host='localhost',
                           port=6064, group='system', secure=True)
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath',
                        type=str,
                        help='filepath to load xml')
    args = parser.parse_args()
    image_map = {"Image:51": 1405, "Image:52": 1406, "Image:27423": 1404}
    populate_omero(args.filepath, image_map, conn)
