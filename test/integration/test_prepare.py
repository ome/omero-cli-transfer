# Copyright (C) 2022 The Jackson Laboratory
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

from __future__ import division

from omero_cli_transfer import TransferControl
from cli import CLITest
from omero.gateway import BlitzGateway
from pathlib import Path
from ome_types import from_xml, to_xml
from ome_types.model import Project, Dataset, Screen, ImageRef, DatasetRef
from ome_types.model import TagAnnotation, MapAnnotation
from ome_types.model import AnnotationRef, ROI, ROIRef, Rectangle
from ome_types.model.screen import PlateRef
from ome_types.model.map import M, Map

import ezomero
import pytest
import os

TEST_FOLDERS = [
        "test/data/prepare/",
]

TEST_FILELISTS = [
        "test/data/prepare/filelist.txt"
]


class TestPrepare(CLITest):

    def setup_method(self, method):
        super(TestPrepare, self).setup_method(method)
        self.cli.register("transfer", TransferControl, "TEST")
        self.args += ["transfer"]
        self.gw = BlitzGateway(client_obj=self.client)
        self.session = self.client.getSessionId()

    def delete_all(self):
        pjs = self.gw.getObjects("Project")
        for p in pjs:
            pj_id = p.id
            print(f"deleting project {pj_id}")
            self.gw.deleteObjects("Project", [pj_id], deleteAnns=True,
                                  deleteChildren=True, wait=True)
        ds = self.gw.getObjects("Dataset")
        for d in ds:
            ds_id = d.id
            print(f"deleting dataset {ds_id}")
            self.gw.deleteObjects("Dataset", [ds_id], deleteAnns=True,
                                  deleteChildren=True, wait=True)
        scs = self.gw.getObjects("Screen")
        for sc in scs:
            sc_id = sc.id
            print(f"deleting screen {sc_id}")
            self.gw.deleteObjects("Screen", [sc_id], deleteAnns=True,
                                  deleteChildren=True, wait=True)
        pls = self.gw.getObjects("Plate")
        for pl in pls:
            pl_id = pl.id
            print(f"deleting plate {pl_id}")
            self.gw.deleteObjects("Plate", [pl_id], deleteAnns=True,
                                  deleteChildren=True, wait=True)
        ims = self.gw.getObjects("Image")
        im_ids = []
        for im in ims:
            im_ids.append(im.id)
            print(f"deleting image {im.id}")
        if im_ids:
            self.gw.deleteObjects("Image", im_ids, deleteAnns=True,
                                  deleteChildren=True, wait=True)

    def test_non_existing_folder(self):
        self.args += ["prepare", "./fakefoldername/"]
        with pytest.raises(ValueError):
            self.cli.invoke(self.args, strict=True)

    @pytest.mark.parametrize('folder', sorted(TEST_FOLDERS))
    def test_prepare_clean(self, folder):
        folder = Path(folder)
        if Path(folder / 'transfer.xml').exists():
            print('transfer.xml exists! deleting.')
            os.remove(str(folder / 'transfer.xml'))
        args = self.args + ["prepare", str(folder)]
        self.cli.invoke(args, strict=True)
        assert Path(folder / 'transfer.xml').exists()
        assert os.path.getsize(str(folder / 'transfer.xml')) > 0
        args = self.args + ["unpack", "--folder", str(folder)]
        self.cli.invoke(args, strict=True)
        self.run_asserts_clean()
        self.delete_all()
        if Path(folder / 'transfer.xml').exists():
            os.remove(str(folder / 'transfer.xml'))

    @pytest.mark.parametrize('folder', sorted(TEST_FOLDERS))
    def test_prepare_edited(self, folder):
        folder = Path(folder)
        if Path(folder / 'transfer.xml').exists():
            os.remove(str(folder / 'transfer.xml'))
        args = self.args + ["prepare", str(folder)]
        self.cli.invoke(args, strict=True)
        assert os.path.exists(str(folder / 'transfer.xml'))
        assert os.path.getsize(str(folder / 'transfer.xml')) > 0
        self.edit_xml(str(folder / 'transfer.xml'))
        args = self.args + ["unpack", "--folder", str(folder)]
        self.cli.invoke(args, strict=True)
        self.run_asserts_edited()
        self.delete_all()
        if Path(folder / 'transfer.xml').exists():
            os.remove(str(folder / 'transfer.xml'))

    @pytest.mark.parametrize('filelist', sorted(TEST_FILELISTS))
    def test_prepare_filelist(self, filelist):
        folder = Path(filelist).parent
        if Path(folder / 'transfer.xml').exists():
            print('transfer.xml exists! deleting.')
            os.remove(str(folder / 'transfer.xml'))
        args = self.args + ["prepare", "--filelist", str(filelist)]
        self.cli.invoke(args, strict=True)
        assert Path(folder / 'transfer.xml').exists()
        assert os.path.getsize(str(folder / 'transfer.xml')) > 0
        args = self.args + ["unpack", "--folder", str(folder)]
        self.cli.invoke(args, strict=True)
        self.run_asserts_filelist()
        self.delete_all()
        if Path(folder / 'transfer.xml').exists():
            os.remove(str(folder / 'transfer.xml'))

    def run_asserts_clean(self):
        img_ids = ezomero.get_image_ids(self.gw)
        assert len(img_ids) == 3
        img_names = []
        for i in (img_ids):
            img, _ = ezomero.get_image(self.gw, i, no_pixels=True)
            img_names.append(img.getName())
        assert "vsi-ets-test-jpg2k.vsi [macro image]" in img_names

    def run_asserts_filelist(self):
        img_ids = ezomero.get_image_ids(self.gw)
        assert len(img_ids) == 1
        img_names = []
        for i in (img_ids):
            img, _ = ezomero.get_image(self.gw, i, no_pixels=True)
            img_names.append(img.getName())
        assert "vsi-ets-test-jpg2k.vsi [macro image]" not in img_names
        assert "test_pyramid.tiff" in img_names

    def run_asserts_edited(self):
        img_ids = ezomero.get_image_ids(self.gw)
        assert len(img_ids) == 0
        proj_ids = ezomero.get_project_ids(self.gw)
        assert len(proj_ids) == 1
        ds_ids = ezomero.get_dataset_ids(self.gw, proj_ids[0])
        assert len(ds_ids) == 1
        img_ids = ezomero.get_image_ids(self.gw, dataset=ds_ids[0])
        img_names = []
        for i in (img_ids):
            img, _ = ezomero.get_image(self.gw, i, no_pixels=True)
            img_name = img.getName()
            img_names.append(img_name)
            if img_name == "test_pyramid.tiff":
                tags = ezomero.get_tag_ids(self.gw, "Image", img.getId())
                assert len(tags) == 1
                tag = ezomero.get_tag(self.gw, tags[0])
                assert tag == "tag for img"
            elif img_name == "edited image name":
                kvs = ezomero.get_map_annotation_ids(self.gw, "Image",
                                                     img.getId())
                assert len(kvs) == 1
                kv = ezomero.get_map_annotation(self.gw, kvs[0])
                assert len(kv) == 2
                assert kv['key1'] == "value1"
                assert kv['key2'] == "2"
            elif img_name == "vsi-ets-test-jpg2k.vsi [macro image]":
                rois = ezomero.get_roi_ids(self.gw, img.getId())
                assert len(rois) == 1
                shapes = ezomero.get_shape_ids(self.gw, rois[0])
                assert len(shapes) == 1
                shape = ezomero.get_shape(self.gw, shapes[0])
                assert type(shape) == ezomero.rois.Rectangle
                assert shape.x == 1
                assert shape.y == 2
                assert shape.width == 3
                assert shape.height == 4
        assert "vsi-ets-test-jpg2k.vsi [macro image]" in img_names
        scr_ids = []
        pl_ids = []
        for screen in self.gw.getObjects("Screen"):
            scr_ids.append(screen.getId())
            for plate in screen.listChildren():
                pl_ids.append(plate.getId())
        assert len(scr_ids) == 1
        assert len(pl_ids) == 1

    def edit_xml(self, filename):
        ome = from_xml(filename, parser='xmlschema')
        new_proj = Project(id="Project:1", name="edited project")
        new_ds = Dataset(id="Dataset:1", name="edited dataset")
        newtag1 = TagAnnotation(id="Annotation:1", value="tag for proj")
        newtag2 = TagAnnotation(id="Annotation:2", value="tag for img")
        new_proj.annotation_ref.append(AnnotationRef(id=newtag1.id))
        md_dict = {"key1": "value1", "key2": 2}
        mmap = []
        for _key, _value in md_dict.items():
            if _value:
                mmap.append(M(k=_key, value=str(_value)))
            else:
                mmap.append(M(k=_key, value=''))
        mapann = MapAnnotation(id="Annotation:3", value=Map(m=mmap))
        rect = Rectangle(id="Shape:1", x=1, y=2, width=3, height=4)
        roi = ROI(id="ROI:1", union=[rect])
        ome.rois.append(roi)
        ome.structured_annotations.extend([newtag1, newtag2, mapann])
        for img in ome.images:
            if img.name == "test_pyramid.tiff":
                img.annotation_ref.append(AnnotationRef(id=newtag2.id))
                imref = ImageRef(id=img.id)
                new_ds.image_ref.append(imref)
            elif img.name == "vsi-ets-test-jpg2k.vsi [001 C405, C488]":
                img.name = "edited image name"
                img.annotation_ref.append(AnnotationRef(id=mapann.id))
                imref = ImageRef(id=img.id)
                new_ds.image_ref.append(imref)
            elif img.name == "vsi-ets-test-jpg2k.vsi [macro image]":
                img.roi_ref.append(ROIRef(id=roi.id))
                imref = ImageRef(id=img.id)
                new_ds.image_ref.append(imref)
        dsref = DatasetRef(id=new_ds.id)
        new_proj.dataset_ref.append(dsref)
        ome.projects.append(new_proj)
        ome.datasets.append(new_ds)
        new_scr = Screen(id="Screen:1", name="edited screen")
        new_scr.plate_ref.append(PlateRef(id=ome.plates[0].id))
        ome.screens.append(new_scr)
        with open(filename, 'w') as fp:
            print(to_xml(ome), file=fp)
            fp.close()
