# Copyright (C) 2022 The Jackson Laboratory
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

from __future__ import division

from omero_cli_transfer import TransferControl
from cli import CLITest
from omero.gateway import BlitzGateway

import ezomero
import pytest
import os
import tarfile

SUPPORTED = [
    "idonly", "imageid", "datasetid", "projectid", "plateid", "screenid"]

TEST_FILES = [
        "test/data/valid_single_image.tar",
        "test/data/valid_single_image.zip",
        "test/data/valid_single_dataset.zip",
        "test/data/valid_single_project.zip",
        "test/data/incomplete_project.zip",
        "test/data/simple_plate.zip",
        "test/data/simple_screen.zip",
]

TEST_FOLDERS = [
        "test/data/valid_single_image/"
]


class TestTransfer(CLITest):

    def setup_method(self, method):
        super(TestTransfer, self).setup_method(method)
        self.cli.register("transfer", TransferControl, "TEST")
        self.args += ["transfer"]
        self.idonly = "-1"
        self.imageid = "Image:-1"
        self.datasetid = "Dataset:-1"
        self.projectid = "Project:-1"
        self.plateid = "Project:-1"
        self.screenid = "Project:-1"
        self.gw = BlitzGateway(client_obj=self.client)

    def create_image(self, sizec=4, sizez=1, sizet=1, target_name=None):
        images = self.import_fake_file(
                images_count=2, sizeZ=sizez, sizeT=sizet, sizeC=sizec,
                client=self.client)
        images.append(self.create_test_image(100, 100, 1, 1, 1,
                                             self.client.getSession()))
        self.imageid = "Image:%s" % images[0].id.val
        self.source = "Image:%s" % images[1].id.val
        for image in images:
            img = self.gw.getObject("Image", image.id.val)
            img.getThumbnail(size=(96,), direct=False)
        if target_name == "datasetid" or target_name == "projectid" or\
           target_name == "idonly":
            # Create Project/Dataset hierarchy
            project = self.make_project(client=self.client)
            self.project = self.gw.getObject("Project", project.id.val)
            dataset = self.make_dataset(client=self.client)
            self.dataset = self.gw.getObject("Dataset", dataset.id.val)
            self.projectid = "Project:%s" % self.project.id
            self.datasetid = "Dataset:%s" % self.dataset.id
            self.idonly = "%s" % self.project.id
            self.link(obj1=project, obj2=dataset)
            for i in images:
                self.link(obj1=dataset, obj2=i)

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

    def create_plate(self, plates=2, target_name=None):
        plates = self.import_plates(plates=plates, client=self.client)
        self.plateid = "Plate:%s" % plates[0].id.val
        screen = ezomero.post_screen(self.gw, "test_screen")
        self.screen = self.gw.getObject("Screen", screen)
        self.screenid = "Screen:%s" % self.screen.id
        for p in plates:
            self.link(obj1=self.screen, obj2=p)

    @pytest.mark.parametrize('target_name', sorted(SUPPORTED))
    def test_non_existing_object(self, target_name, tmpdir):
        self.args += ["pack", getattr(self, target_name),
                      str(tmpdir / 'test.zip')]
        with pytest.raises(ValueError):
            self.cli.invoke(self.args, strict=True)

    @pytest.mark.parametrize('target_name', sorted(SUPPORTED))
    def test_pack(self, target_name, tmpdir):
        if target_name == "datasetid" or target_name == "projectid" or\
           target_name == "idonly" or target_name == "imageid":
            self.create_image(target_name=target_name)
        elif target_name == "plateid" or target_name == "screenid":
            self.create_plate(target_name=target_name)
        target = getattr(self, target_name)
        args = self.args + ["pack", target, str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        assert os.path.exists(str(tmpdir / 'test.tar'))
        assert os.path.getsize(str(tmpdir / 'test.tar')) > 0
        args = self.args + ["pack", target, "--zip", str(tmpdir / 'test.zip')]
        self.cli.invoke(args, strict=True)
        assert os.path.exists(str(tmpdir / 'test.zip'))
        assert os.path.getsize(str(tmpdir / 'test.zip')) > 0
        args = self.args + ["pack", target, "--barchive",
                            str(tmpdir / 'testba.tar')]
        if target_name == "datasetid" or target_name == "projectid" \
           or target_name == "idonly":
            self.cli.invoke(args, strict=True)
            assert os.path.exists(str(tmpdir / 'testba.tar'))
            assert os.path.getsize(str(tmpdir / 'testba.tar')) > 0
        else:
            with pytest.raises(ValueError):
                self.cli.invoke(args, strict=True)
        self.delete_all()

    @pytest.mark.parametrize('target_name', sorted(SUPPORTED))
    def test_pack_special(self, target_name, tmpdir):
        if target_name == "datasetid" or target_name == "projectid" or\
           target_name == "idonly" or target_name == "imageid":
            self.create_image(target_name=target_name)
        elif target_name == "plateid" or target_name == "screenid":
            self.create_plate(target_name=target_name)
        target = getattr(self, target_name)
        args = self.args + ["pack", target, "--barchive",
                            str(tmpdir / 'testba.tar')]
        if target_name == "datasetid" or target_name == "projectid" \
           or target_name == "idonly":
            self.cli.invoke(args, strict=True)
            assert os.path.exists(str(tmpdir / 'testba.tar'))
            assert os.path.getsize(str(tmpdir / 'testba.tar')) > 0
        else:
            with pytest.raises(ValueError):
                self.cli.invoke(args, strict=True)
        args = self.args + ["pack", target, "--simple",
                            str(tmpdir / 'testsimple.tar')]
        if target_name == "plateid" or target_name == "screenid":
            with pytest.raises(ValueError):
                self.cli.invoke(args, strict=True)
        else:
            self.cli.invoke(args, strict=True)
            assert os.path.exists(str(tmpdir / 'testsimple.tar'))
            assert os.path.getsize(str(tmpdir / 'testsimple.tar')) > 0
            f = tarfile.open(str(tmpdir / 'testsimple.tar'), "r")
            if target_name == "datasetid":
                # `./`, ds folder, 2 files, transfer.xml
                assert len(f.getmembers()) == 5
            elif target_name == "imageid":
                # `./`, 1 file, transfer.xml
                assert len(f.getmembers()) == 3
            else:
                # `./`, proj folder, ds folder, 2 files, transfer.xml
                assert len(f.getmembers()) == 6
        self.delete_all()

    @pytest.mark.parametrize('folder_name', TEST_FOLDERS)
    def test_unpack_folder(self, folder_name):
        self.args += ["unpack", "--folder", folder_name]
        self.cli.invoke(self.args, strict=True)
        if folder_name == "test/data/valid_single_image/":
            im_ids = ezomero.get_image_ids(self.gw)
            assert len(im_ids) == 1
            img, _ = ezomero.get_image(self.gw, im_ids[-1])
            assert img.getName() == 'combined_result.tiff'
            assert len(ezomero.get_roi_ids(self.gw, im_ids[-1])) == 3
            map_ann_ids = ezomero.get_map_annotation_ids(
                            self.gw, "Image", im_ids[-1])
            assert len(map_ann_ids) == 3
            for annid in map_ann_ids:
                ann_obj = self.gw.getObject("MapAnnotation", annid)
                ann = ezomero.get_map_annotation(self.gw, annid)
                if ann_obj.getNs() == "openmicroscopy.org/cli/transfer":
                    assert len(ann) == 8
            assert len(ezomero.get_tag_ids(
                            self.gw, "Image", im_ids[-1])) == 1
        self.delete_all()

        temp_args = self.args
        self.args += ["--metadata", "none", "db_id"]
        self.cli.invoke(self.args, strict=True)
        if folder_name == "test/data/valid_single_image/":
            im_ids = ezomero.get_image_ids(self.gw)
            assert len(im_ids) == 1
            map_ann_ids = ezomero.get_map_annotation_ids(
                            self.gw, "Image", im_ids[-1])
            assert len(map_ann_ids) == 3
            for annid in map_ann_ids:
                ann_obj = self.gw.getObject("MapAnnotation", annid)
                ann = ezomero.get_map_annotation(self.gw, annid)
                if ann_obj.getNs() == "openmicroscopy.org/cli/transfer":
                    assert len(ann) == 1
        self.delete_all()

        self.args = temp_args + ["--metadata", "orig_user", "db_id"]
        self.cli.invoke(self.args, strict=True)
        if folder_name == "test/data/valid_single_image/":
            im_ids = ezomero.get_image_ids(self.gw)
            assert len(im_ids) == 1
            map_ann_ids = ezomero.get_map_annotation_ids(
                            self.gw, "Image", im_ids[-1])
            assert len(map_ann_ids) == 3
            for annid in map_ann_ids:
                ann_obj = self.gw.getObject("MapAnnotation", annid)
                ann = ezomero.get_map_annotation(self.gw, annid)
                if ann_obj.getNs() == "openmicroscopy.org/cli/transfer":
                    assert len(ann) == 1
        self.delete_all()

    @pytest.mark.parametrize('package_name', TEST_FILES)
    def test_unpack(self, package_name):
        self.args += ["unpack", package_name]
        self.cli.invoke(self.args, strict=True)

        if package_name == "test/data/valid_single_image.tar":
            im_ids = ezomero.get_image_ids(self.gw)
            assert len(im_ids) == 1
            img, _ = ezomero.get_image(self.gw, im_ids[-1])
            assert img.getName() == 'combined_result.tiff'
            assert len(ezomero.get_roi_ids(self.gw, im_ids[-1])) == 3
            assert len(ezomero.get_map_annotation_ids(
                            self.gw, "Image", im_ids[-1])) == 3
            assert len(ezomero.get_tag_ids(
                            self.gw, "Image", im_ids[-1])) == 1
            self.delete_all()

        if package_name == "test/data/valid_single_image.zip":
            im_ids = ezomero.get_image_ids(self.gw)
            assert len(im_ids) == 1
            img, _ = ezomero.get_image(self.gw, im_ids[-1])
            assert img.getName() == 'combined_result.tiff'
            assert len(ezomero.get_roi_ids(self.gw, im_ids[-1])) == 3
            assert len(ezomero.get_map_annotation_ids(
                            self.gw, "Image", im_ids[-1])) == 3
            assert len(ezomero.get_tag_ids(
                            self.gw, "Image", im_ids[-1])) == 1
            self.delete_all()

        if package_name == "test/data/valid_single_dataset.zip":
            ds = self.gw.getObjects("Dataset", opts={'orphaned': True})
            count = 0
            for d in ds:
                ds_id = d.getId()
                count += 1
            assert count == 1
            im_ids = ezomero.get_image_ids(self.gw, dataset=ds_id)
            assert len(im_ids) == 1
            assert len(ezomero.get_map_annotation_ids(
                            self.gw, "Dataset", ds_id)) == 1
            assert len(ezomero.get_tag_ids(
                            self.gw, "Dataset", ds_id)) == 2
            self.delete_all()

        if package_name == "test/data/valid_single_project.zip":
            ezomero.print_projects(self.gw)
            pjs = self.gw.getObjects("Project")
            count = 0
            for p in pjs:
                pj_id = p.getId()
                count += 1
            assert count == 1
            count = 0
            proj = self.gw.getObject("Project", pj_id)
            for d in proj.listChildren():
                ds_id = d.getId()
                count += 1
            assert count == 2
            im_ids = ezomero.get_image_ids(self.gw, dataset=ds_id)
            assert len(im_ids) == 1
            assert len(ezomero.get_map_annotation_ids(
                            self.gw, "Project", pj_id)) == 1
            assert len(ezomero.get_tag_ids(
                            self.gw, "Project", pj_id)) == 0
            self.delete_all()

        if package_name == "test/data/incomplete_project.zip":
            ezomero.print_projects(self.gw)
            pjs = ezomero.get_project_ids(self.gw)
            assert len(pjs) == 1
            ds_ids = ezomero.get_dataset_ids(self.gw, pjs[-1])
            ds_ids.sort()
            assert len(ds_ids) == 2
            im_ids = ezomero.get_image_ids(self.gw, dataset=ds_ids[0])
            assert len(im_ids) == 2
            im_ids = ezomero.get_image_ids(self.gw, dataset=ds_ids[1])
            assert len(im_ids) == 0
            self.delete_all()

        if package_name == "test/data/simple_plate.zip":
            pls = self.gw.getObjects("Plate", opts={'orphaned': True})
            count = 0
            for p in pls:
                pl_id = p.getId()
                count += 1
            assert count == 1
            pl = self.gw.getObject("Plate", pl_id)
            wells = pl.listChildren()
            count = 0
            for well in wells:
                well_id = well.getId()
                count += 1
            assert count == 1
            well = self.gw.getObject("Well", well_id)
            index = well.countWellSample()
            assert index == 1
            self.delete_all()

        if package_name == "test/data/simple_screen.zip":
            scs = self.gw.getObjects("Screen")
            count = 0
            for s in scs:
                sc_id = s.getId()
                count += 1
            assert count == 1
            count = 0
            scr = self.gw.getObject("Screen", sc_id)
            for p in scr.listChildren():
                pl_id = p.getId()
                count += 1
            assert count == 2
            assert len(ezomero.get_tag_ids(
                            self.gw, "Screen", sc_id)) == 1
            self.delete_all()

    def test_unpack_skip(self):
        self.args += ["unpack", "test/data/valid_single_image.tar"]
        self.args += ["--skip", "all"]
        self.cli.invoke(self.args, strict=True)
        im_ids = ezomero.get_image_ids(self.gw)
        assert len(im_ids) == 1
        img, _ = ezomero.get_image(self.gw, im_ids[-1])
        assert img.getName() == 'combined_result.tiff'
        self.delete_all()

    def test_unpack_merge(self):
        proj_args = self.args + ["unpack",
                                 "test/data/valid_single_project.zip"]
        self.cli.invoke(proj_args, strict=True)
        proj_args += ['--merge']
        self.cli.invoke(proj_args, strict=True)
        pj_ids = ezomero.get_project_ids(self.gw)
        assert len(pj_ids) == 1
        ds_ids = ezomero.get_dataset_ids(self.gw, pj_ids[0])
        assert len(ds_ids) == 2
        ds_args = self.args + ['unpack', "test/data/valid_single_dataset.zip"]
        print(ds_args)
        self.cli.invoke(ds_args, strict=True)
        orphan = ezomero.get_dataset_ids(self.gw)
        assert len(orphan) == 1
        ds_args += ['--merge']
        self.cli.invoke(ds_args, strict=True)
        orphan = ezomero.get_dataset_ids(self.gw)
        assert len(orphan) == 1
        scr_args = self.args + ['unpack', "test/data/simple_screen.zip"]
        self.cli.invoke(scr_args, strict=True)
        scr_args += ['--merge']
        self.cli.invoke(scr_args, strict=True)
        scr_ids = []
        for screen in self.gw.getObjects("Screen"):
            scr_ids.append(screen.getId())
        assert len(scr_ids) == 1
        pl_ids = []
        screen = self.gw.getObject("Screen", scr_ids[0])
        for plate in screen.listChildren():
            pl_ids.append(plate.getId())
        assert len(pl_ids) == 4
        self.delete_all()

    @pytest.mark.parametrize('target_name', sorted(SUPPORTED))
    def test_pack_unpack(self, target_name, tmpdir):
        if target_name == "datasetid" or target_name == "projectid" or\
           target_name == "idonly" or target_name == "imageid":
            self.create_image(target_name=target_name)
        elif target_name == "plateid" or target_name == "screenid":
            self.create_plate(plates=1, target_name=target_name)
        target = getattr(self, target_name)
        args = self.args + ["pack", target, str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        self.delete_all()
        args = self.args + ["unpack", str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        self.run_asserts(target_name)
        self.delete_all()

        if target_name == "datasetid" or target_name == "projectid" or\
           target_name == "idonly" or target_name == "imageid":
            self.create_image(target_name=target_name)
        elif target_name == "plateid" or target_name == "screenid":
            self.create_plate(plates=1, target_name=target_name)
        target = getattr(self, target_name)
        args = self.args + ["pack", target, "--zip", str(tmpdir / 'test.zip')]
        self.cli.invoke(args, strict=True)
        self.delete_all()
        args = self.args + ["unpack", str(tmpdir / 'test.zip')]
        self.cli.invoke(args, strict=True)
        self.run_asserts(target_name)
        self.delete_all()

    def run_asserts(self, target_name):
        if target_name == "imageid":
            img_ids = ezomero.get_image_ids(self.gw)
            assert len(img_ids) == 2
        if target_name == "projectid" or target_name == "idonly":
            pjs = self.gw.getObjects("Project")
            count = 0
            for p in pjs:
                pj_id = p.getId()
                count += 1
            assert count == 1
            count = 0
            proj = self.gw.getObject("Project", pj_id)
            for d in proj.listChildren():
                ds_id = d.getId()
                count += 1
            assert count == 1
            im_ids = ezomero.get_image_ids(self.gw, dataset=ds_id)
            assert len(im_ids) == 3
        if target_name == "datasetid":
            ds = self.gw.getObjects("Dataset", opts={'orphaned': True})
            count = 0
            for d in ds:
                ds_id = d.getId()
                count += 1
            assert count == 1
            im_ids = ezomero.get_image_ids(self.gw, dataset=ds_id)
            assert len(im_ids) == 3
        if target_name == "screenid":
            scs = self.gw.getObjects("Screen")
            count = 0
            for s in scs:
                sc_id = s.getId()
                count += 1
            assert count == 1
            count = 0
            scr = self.gw.getObject("Screen", sc_id)
            for p in scr.listChildren():
                pl_id = p.getId()
                count += 1
            assert count == 1
            pl = self.gw.getObject("Plate", pl_id)
            wells = pl.listChildren()
            count = 0
            for well in wells:
                well_id = well.getId()
                count += 1
            assert count == 1
            well = self.gw.getObject("Well", well_id)
            index = well.countWellSample()
            assert index == 1
        if target_name == "plate_id":
            pls = self.gw.getObjects("Plate", opts={'orphaned': True})
            count = 0
            for p in pls:
                pl_id = p.getId()
                count += 1
            assert count == 1
            pl = self.gw.getObject("Plate", pl_id)
            wells = pl.listChildren()
            count = 0
            for well in wells:
                well_id = well.getId()
                count += 1
            assert count == 1
            well = self.gw.getObject("Well", well_id)
            index = well.countWellSample()
            assert index == 1
