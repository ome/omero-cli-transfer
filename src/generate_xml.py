from ome_types import to_xml, OME
from ome_types.model import Project, ProjectRef
from ome_types.model import Screen
from ome_types.model.screen import PlateRef
from ome_types.model import Well, WellSample
from ome_types.model import Plate
from ome_types.model import Dataset, DatasetRef
from ome_types.model import Image, ImageRef, Pixels
from ome_types.model import TagAnnotation, MapAnnotation, ROI
from ome_types.model import FileAnnotation, BinaryFile, BinData
from ome_types.model import AnnotationRef, ROIRef, Map
from ome_types.model import CommentAnnotation, LongAnnotation
from ome_types.model import Point, Line, Rectangle, Ellipse, Polygon
from ome_types.model import Polyline, Label, Shape
from ome_types.model.map import M
from omero.gateway import BlitzGateway
from omero.model import TagAnnotationI, MapAnnotationI, FileAnnotationI
from omero.model import CommentAnnotationI, LongAnnotationI, Fileset
from omero.model import PointI, LineI, RectangleI, EllipseI, PolygonI
from omero.model import PolylineI, LabelI, ImageI, RoiI, IObject
from omero.model import DatasetI, ProjectI, ScreenI, PlateI, WellI, Annotation
from typing import Tuple, List, Optional, Union, Any, Dict, TextIO
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
    pol = Polyline(**args)
    return pol


def create_label(shape: LabelI) -> Label:
    args = {'id': shape.getId().val, 'x': shape.getX().val,
            'y': shape.getY().val}
    args['text'] = shape.getTextValue().val
    args['font_size'] = shape.getFontSize().getValue()
    args['the_c'] = 0
    args['the_z'] = 0
    args['the_t'] = 0
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
            print("not a real thing")
            continue
    return shapes


def create_filepath_annotations(id: str, conn: BlitzGateway,
                                filename: Union[str,
                                                PathLike] = ".",
                                plate_path: Optional[str] = None
                                ) -> Tuple[List[CommentAnnotation],
                                           List[AnnotationRef]]:
    ns = id
    anns = []
    anrefs = []
    fp_type = ns.split(":")[0]
    clean_id = int(ns.split(":")[-1])
    if fp_type == "Image":
        fpaths = ezomero.get_original_filepaths(conn, clean_id)
        if len(fpaths) > 1:
            allpaths = []
            for f in fpaths:
                f = Path(f)
                allpaths.append(f.parts)
            common_root = Path(*os.path.commonprefix(allpaths))
            path = os.path.join(common_root, 'mock_folder')
            uid = (-1) * uuid4().int
            an = CommentAnnotation(id=uid,
                                   namespace=ns,
                                   value=str(path)
                                   )
            anns.append(an)
            anref = AnnotationRef(id=an.id)
            anrefs.append(anref)
        else:
            if fpaths:
                f = fpaths[0]
            else:
                f = f'pixel_images/{clean_id}.tiff'

            uid = (-1) * uuid4().int
            an = CommentAnnotation(id=uid,
                                   namespace=ns,
                                   value=f
                                   )
            anns.append(an)
            anref = AnnotationRef(id=an.id)
            anrefs.append(anref)
    elif fp_type == "Annotation":
        filename = str(Path(filename).name)
        f = f'file_annotations/{clean_id}/{filename}'
        uid = (-1) * uuid4().int
        an = CommentAnnotation(id=uid,
                               namespace=ns,
                               value=f
                               )
        anns.append(an)
        anref = AnnotationRef(id=an.id)
        anrefs.append(anref)
    elif fp_type == "Plate":
        uid = (-1) * uuid4().int
        an = CommentAnnotation(id=uid,
                               namespace=ns,
                               value=plate_path
                               )
        anns.append(an)
        anref = AnnotationRef(id=an.id)
        anrefs.append(anref)
    return anns, anrefs


def create_provenance_metadata(conn: BlitzGateway, img_id: int,
                               hostname: str,
                               metadata: Union[List[str], None]
                               ) -> Union[Tuple[MapAnnotation, AnnotationRef],
                                          Tuple[None, None]]:
    if not metadata:
        return None, None
    software = "omero-cli-transfer"
    version = pkg_resources.get_distribution(software).version
    date_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    ns = 'openmicroscopy.org/cli/transfer'
    curr_user = conn.getUser().getName()
    curr_group = conn.getGroupFromContext().getName()
    id = (-1) * uuid4().int
    db_id = conn.getConfigService().getDatabaseUuid()

    md_dict: Dict[str, Any] = {}
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

    mmap = []
    for _key, _value in md_dict.items():
        if _value:
            mmap.append(M(k=_key, value=str(_value)))
        else:
            mmap.append(M(k=_key, value=''))
    kv, ref = create_kv_and_ref(id=id,
                                namespace=ns,
                                value=Map(m=mmap))
    return kv, ref


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
                   metadata: List[str], fset: Union[None, Fileset] = None
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
    kv, ref = create_provenance_metadata(conn, id, hostname, metadata)
    if kv:
        kv_id = f"Annotation:{str(kv.id)}"
        if kv_id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(kv)
        if ref:
            img.annotation_ref.append(ref)
    filepath_anns, refs = create_filepath_annotations(img_id, conn)
    for i in range(len(filepath_anns)):
        ome.structured_annotations.append(filepath_anns[i])
        img.annotation_ref.append(refs[i])
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
                populate_image(fs_image, ome, conn, hostname, metadata, fset)
    return img_ref


def populate_dataset(obj: DatasetI, ome: OME, conn: BlitzGateway,
                     hostname: str, metadata: List[str]) -> DatasetRef:
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    ds, ds_ref = create_dataset_and_ref(id=id, name=name,
                                        description=desc)
    for ann in obj.listAnnotations():
        add_annotation(ds, ann, ome, conn)
    for img in obj.listChildren():
        img_obj = conn.getObject('Image', img.getId())
        img_ref = populate_image(img_obj, ome, conn, hostname, metadata)
        ds.image_ref.append(img_ref)
    ds_id = f"Dataset:{str(ds.id)}"
    if ds_id not in [i.id for i in ome.datasets]:
        ome.datasets.append(ds)
    return ds_ref


def populate_project(obj: ProjectI, ome: OME, conn: BlitzGateway,
                     hostname: str, metadata: List[str]):
    id = obj.getId()
    name = obj.getName()
    desc = obj.getDescription()
    proj, _ = create_proj_and_ref(id=id, name=name, description=desc)
    for ann in obj.listAnnotations():
        add_annotation(proj, ann, ome, conn)
    for ds in obj.listChildren():
        ds_obj = conn.getObject('Dataset', ds.getId())
        ds_ref = populate_dataset(ds_obj, ome, conn, hostname, metadata)
        proj.dataset_ref.append(ds_ref)
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
        scr.plate_ref.append(pl_ref)
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
    for well in obj.listChildren():
        well_obj = conn.getObject('Well', well.getId())
        well_ref = populate_well(well_obj, ome, conn, hostname, metadata)
        pl.wells.append(well_ref)
    last_image_anns = ome.images[-1].annotation_ref
    last_image_anns_ids = [i.id for i in last_image_anns]
    for ann in ome.structured_annotations:
        if (ann.id in last_image_anns_ids and
                type(ann) == CommentAnnotation and
                int(ann.id.split(":")[-1]) < 0):
            plate_path = ann.value
    filepath_anns, refs = create_filepath_annotations(pl.id, conn,
                                                      plate_path=plate_path)
    for i in range(len(filepath_anns)):
        ome.structured_annotations.append(filepath_anns[i])
        pl.annotation_ref.append(refs[i])
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
        ws_img_ref = populate_image(ws_img, ome, conn, hostname, metadata)
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
                                    m=mmap))
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
                                filename=ann.getFile().getName())
        for i in range(len(filepath_anns)):
            ome.structured_annotations.append(filepath_anns[i])
            f.annotation_ref.append(refs[i])
        if f.id not in [i.id for i in ome.structured_annotations]:
            ome.structured_annotations.append(f)
        obj.annotation_ref.append(ref)


def list_file_ids(ome: OME) -> dict:
    id_list = {}
    for ann in ome.structured_annotations:
        clean_id = int(ann.id.split(":")[-1])
        if isinstance(ann, CommentAnnotation) and clean_id < 0:
            id_list[ann.namespace] = ann.value
    return id_list


def populate_xml(datatype: str, id: int, filepath: str, conn: BlitzGateway,
                 hostname: str, barchive: bool,
                 metadata: List[str]) -> Tuple[OME, dict]:
    ome = OME()
    obj = conn.getObject(datatype, id)
    if datatype == 'Project':
        populate_project(obj, ome, conn, hostname, metadata)
    elif datatype == 'Dataset':
        populate_dataset(obj, ome, conn, hostname, metadata)
    elif datatype == 'Image':
        populate_image(obj, ome, conn, hostname, metadata)
    elif datatype == 'Screen':
        populate_screen(obj, ome, conn, hostname, metadata)
    elif datatype == 'Plate':
        populate_plate(obj, ome, conn, hostname, metadata)
    if not barchive:
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
        for ann_ref in i.annotation_ref:
            ann = next(filter(lambda x: x.id == ann_ref.id, anns))
            if isinstance(ann, MapAnnotation):
                for v in ann.value.m:
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
        if any(filter(lfunc, d.image_ref)):
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
    for annref in img.annotation_ref:
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
