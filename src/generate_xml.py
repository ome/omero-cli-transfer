from ome_types import to_xml, OME
from ome_types.model import Project, ProjectRef
from ome_types.model import Dataset, DatasetRef
from ome_types.model import Image, ImageRef, Pixels
from ome_types.model import TagAnnotation, MapAnnotation, ROI
from ome_types.model import AnnotationRef, ROIRef, Map
from ome_types.model import CommentAnnotation
from ome_types.model import Point, Line, Rectangle, Ellipse, Polygon
from ome_types.model.map import M
from omero.model import TagAnnotationI, MapAnnotationI
from omero.model import PointI, LineI, RectangleI, EllipseI, PolygonI
import pkg_resources
import ezomero
import os
from uuid import uuid4
from datetime import datetime


def create_proj_and_ref(**kwargs):
    proj = Project(**kwargs)
    proj_ref = ProjectRef(id=proj.id)
    return proj, proj_ref


def create_dataset_and_ref(**kwargs):
    ds = Dataset(**kwargs)
    ds_ref = DatasetRef(id=ds.id)
    return ds, ds_ref


def create_pixels(obj):
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


def create_image_and_ref(**kwargs):
    img = Image(**kwargs)
    img_ref = ImageRef(id=img.id)
    return img, img_ref


def create_tag_and_ref(**kwargs):
    tag = TagAnnotation(**kwargs)
    tagref = AnnotationRef(id=tag.id)
    return tag, tagref


def create_kv_and_ref(**kwargs):
    kv = MapAnnotation(**kwargs)
    kvref = AnnotationRef(id=kv.id)
    return kv, kvref


def create_roi_and_ref(**kwargs):
    roi = ROI(**kwargs)
    roiref = ROIRef(id=roi.id)
    return roi, roiref


def create_point(shape):
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
    pt = Point(**args)
    return pt


def create_line(shape):
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
    ln = Line(**args)
    return ln


def create_rectangle(shape):
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
    rec = Rectangle(**args)
    return rec


def create_ellipse(shape):
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
    ell = Ellipse(**args)
    return ell


def create_polygon(shape):
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
    pol = Polygon(**args)
    return pol


def create_shapes(roi):
    shapes = []
    for s in roi.iterateShapes():
        if isinstance(s, PointI):
            p = create_point(s)
            shapes.append(p)
        if isinstance(s, LineI):
            line = create_line(s)
            shapes.append(line)
        if isinstance(s, RectangleI):
            r = create_rectangle(s)
            shapes.append(r)
        if isinstance(s, EllipseI):
            e = create_ellipse(s)
            shapes.append(e)
        if isinstance(s, PolygonI):
            pol = create_polygon(s)
            shapes.append(pol)
        else:
            continue
    return shapes


def create_filepath_annotations(repo, id, conn):
    ns = f'Image:{id}'
    anns = []
    refs = []
    fpaths = ezomero.get_original_filepaths(conn, id)
    for f in fpaths:
        f = str(os.path.join(repo,  '.', f))
        id = (-1) * uuid4().int
        an = CommentAnnotation(id=id,
                               namespace=ns,
                               value=f
                               )
        anns.append(an)
        anref = ROIRef(id=an.id)
        refs.append(anref)
    return anns, refs


def create_provenance_metadata(id, hostname):
    software = "omero-cli-transfer"
    version = pkg_resources.get_distribution(software).version
    date_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    md_dict = {'image_id': id, 'origin_hostname': hostname,
               'packing_timestamp': date_time,
               'software': software, 'version': version}
    ns = 'openmicroscopy.org/cli/transfer'
    id = (-1) * uuid4().int
    mmap = []
    for _key, _value in md_dict:
        if _value:
            mmap.append(M(k=_key, value=str(_value)))
        else:
            mmap.append(M(k=_key, value=''))
    kv, ref = create_kv_and_ref(id=id,
                                namespace=ns,
                                value=Map(m=mmap))
    print(kv, ref)
    return kv, ref


def populate_roi(obj, roi_obj, ome, conn):
    id = obj.getId().getValue()
    name = obj.getName()
    if name is not None:
        name = name.getValue()
    desc = obj.getDescription()
    if desc is not None:
        desc = desc.getValue()
    shapes = create_shapes(obj)
    roi, roi_ref = create_roi_and_ref(id=id, name=name, description=desc,
                                      union=shapes)
    for ann in roi_obj.listAnnotations():
        if ann.OMERO_TYPE == TagAnnotationI:
            tag, ref = create_tag_and_ref(id=ann.getId(),
                                          value=ann.getTextValue())
            if tag not in ome.structured_annotations:
                ome.structured_annotations.append(tag)
            roi.annotation_ref.append(ref)
        if ann.OMERO_TYPE == MapAnnotationI:
            mmap = []
            for _key, _value in ann.getMapValueAsMap().items():
                if _value:
                    mmap.append(M(k=_key, value=str(_value)))
                else:
                    mmap.append(M(k=_key, value=''))
            kv, ref = create_kv_and_ref(id=ann.getId(),
                                        namespace=ann.getNs(),
                                        value=Map(
                                        m=mmap))
            if kv not in ome.structured_annotations:
                ome.structured_annotations.append(kv)
            roi.annotation_ref.append(ref)
    if roi not in ome.rois:
        ome.rois.append(roi)
    return roi_ref


def populate_image(obj, ome, conn, repo, hostname):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    pix = create_pixels(obj)
    img, img_ref = create_image_and_ref(id=id, name=name,
                                        description=desc, pixels=pix)
    for ann in obj.listAnnotations():
        if ann.OMERO_TYPE == TagAnnotationI:
            tag, ref = create_tag_and_ref(id=ann.getId(),
                                          value=ann.getTextValue())
            if tag not in ome.structured_annotations:
                ome.structured_annotations.append(tag)
            img.annotation_ref.append(ref)
        if ann.OMERO_TYPE == MapAnnotationI:
            mmap = []
            for _key, _value in ann.getMapValueAsMap().items():
                if _value:
                    mmap.append(M(k=_key, value=str(_value)))
                else:
                    mmap.append(M(k=_key, value=''))
            kv, ref = create_kv_and_ref(id=ann.getId(),
                                        namespace=ann.getNs(),
                                        value=Map(
                                        m=mmap))
            if kv not in ome.structured_annotations:
                ome.structured_annotations.append(kv)
            img.annotation_ref.append(ref)
    kv, ref = create_provenance_metadata(id, hostname)
    if kv not in ome.structured_annotations:
        ome.structured_annotations.append(kv)
    img.annotation_ref.append(ref)
    filepath_anns, refs = create_filepath_annotations(repo, id, conn)
    for i in range(len(filepath_anns)):
        ome.structured_annotations.append(filepath_anns[i])
        img.annotation_ref.append(refs[i])
    roi_service = conn.getRoiService()
    rois = roi_service.findByImage(id, None).rois
    for roi in rois:
        roi_obj = conn.getObject('Roi', roi.getId().getValue())
        roi_ref = populate_roi(roi, roi_obj, ome, conn)
        img.roi_ref.append(roi_ref)
    if img not in ome.images:
        ome.images.append(img)
    return img_ref


def populate_dataset(obj, ome, conn, repo, hostname):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    ds, ds_ref = create_dataset_and_ref(id=id, name=name,
                                        description=desc)
    for ann in obj.listAnnotations():
        if ann.OMERO_TYPE == TagAnnotationI:
            tag, ref = create_tag_and_ref(id=ann.getId(),
                                          value=ann.getTextValue())
            if tag not in ome.structured_annotations:
                ome.structured_annotations.append(tag)
            ds.annotation_ref.append(ref)
        if ann.OMERO_TYPE == MapAnnotationI:
            mmap = []
            for _key, _value in ann.getMapValueAsMap().items():
                if _value:
                    mmap.append(M(k=_key, value=str(_value)))
                else:
                    mmap.append(M(k=_key, value=''))
            kv, ref = create_kv_and_ref(id=ann.getId(),
                                        namespace=ann.getNs(),
                                        value=Map(
                                        m=mmap))
            if kv not in ome.structured_annotations:
                ome.structured_annotations.append(kv)
            ds.annotation_ref.append(ref)
    for img in obj.listChildren():
        img_obj = conn.getObject('Image', img.getId())
        img_ref = populate_image(img_obj, ome, conn, repo, hostname)
        ds.image_ref.append(img_ref)
    if ds not in ome.datasets:
        ome.datasets.append(ds)
    return ds_ref


def populate_project(obj, ome, conn, repo, hostname):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    test_proj, _ = create_proj_and_ref(id=id, name=name, description=desc)
    for ann in obj.listAnnotations():
        if ann.OMERO_TYPE == TagAnnotationI:
            tag, ref = create_tag_and_ref(id=ann.getId(),
                                          value=ann.getTextValue())
            if tag not in ome.structured_annotations:
                ome.structured_annotations.append(tag)
            test_proj.annotation_ref.append(ref)
        if ann.OMERO_TYPE == MapAnnotationI:
            mmap = []
            for _key, _value in ann.getMapValueAsMap().items():
                if _value:
                    mmap.append(M(k=_key, value=str(_value)))
                else:
                    mmap.append(M(k=_key, value=''))

            kv, ref = create_kv_and_ref(id=ann.getId(),
                                        namespace=ann.getNs(),
                                        value=Map(
                                        m=mmap))
            if kv not in ome.structured_annotations:
                ome.structured_annotations.append(kv)
            test_proj.annotation_ref.append(ref)
    for ds in obj.listChildren():
        ds_obj = conn.getObject('Dataset', ds.getId())
        ds_ref = populate_dataset(ds_obj, ome, conn, repo, hostname)
        test_proj.dataset_ref.append(ds_ref)
    ome.projects.append(test_proj)


def list_image_ids(ome):
    id_list = {}
    for ann in ome.structured_annotations:
        if isinstance(ann, CommentAnnotation):
            id_list[ann.namespace] = ann.value
    return id_list


def populate_xml(datatype, id, filepath, conn, repo, hostname):
    ome = OME()
    obj = conn.getObject(datatype, id)
    if datatype == 'Project':
        populate_project(obj, ome, conn, repo, hostname)
    if datatype == 'Dataset':
        populate_dataset(obj, ome, conn, repo, hostname)
    if datatype == 'Image':
        populate_image(obj, ome, conn, repo, hostname)
    with open(filepath, 'w') as fp:
        print(to_xml(ome), file=fp)
        fp.close()
    path_id_dict = list_image_ids(ome)
    return path_id_dict
