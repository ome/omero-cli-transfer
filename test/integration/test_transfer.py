from __future__ import division

from omero_cli_transfer import TransferControl
from cli import CLITest
from omero.gateway import BlitzGateway

import ezomero
import pytest
import os

SUPPORTED = [
    "idonly", "imageid", "datasetid", "projectid", "plateid", "screenid"]

TEST_FILES = [
        "test/data/valid_single_image.tar",
        "test/data/valid_single_image.zip",
        "test/data/valid_single_dataset.zip",
        "test/data/valid_single_project.zip",
        "test/data/simple_plate.zip",
        "test/data/simple_screen.zip",
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

    def create_plate(self, sizec=4, sizez=1, sizet=1, target_name=None):
        plates = self.import_plates(plates=2, client=self.client)
        self.plateid = "Plate:%s" % plates[0].id.val
        self.source = "Plate:%s" % plates[1].id.val
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

    @pytest.mark.parametrize('package_name', TEST_FILES)
    def test_unpack(self, package_name):
        self.args += ["unpack", package_name]
        self.cli.invoke(self.args, strict=True)

        if package_name == "test/data/valid_single_image.tar":
            im_ids = ezomero.get_image_ids(self.gw)
            assert len(im_ids) == 4
            img, _ = ezomero.get_image(self.gw, im_ids[-1])
            assert img.getName() == 'combined_result.tiff'
            assert len(ezomero.get_roi_ids(self.gw, im_ids[-1])) == 3
            assert len(ezomero.get_map_annotation_ids(
                            self.gw, "Image", im_ids[-1])) == 3
            assert len(ezomero.get_tag_ids(
                            self.gw, "Image", im_ids[-1])) == 1

        if package_name == "test/data/valid_single_image.zip":
            im_ids = ezomero.get_image_ids(self.gw)
            assert len(im_ids) == 5
            img, _ = ezomero.get_image(self.gw, im_ids[-1])
            assert img.getName() == 'combined_result.tiff'
            assert len(ezomero.get_roi_ids(self.gw, im_ids[-1])) == 3
            assert len(ezomero.get_map_annotation_ids(
                            self.gw, "Image", im_ids[-1])) == 3
            assert len(ezomero.get_tag_ids(
                            self.gw, "Image", im_ids[-1])) == 1

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

        if package_name == "test/data/valid_single_project.zip":
            ezomero.print_projects(self.gw)
            pjs = self.gw.getObjects("Project")
            count = 0
            for p in pjs:
                pj_id = p.getId()
                count += 1
            assert count == 4
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

        if package_name == "test/data/simple_screen.zip":
            scs = self.gw.getObjects("Screen")
            count = 0
            for s in scs:
                sc_id = s.getId()
                count += 1
            assert count == 3
            count = 0
            scr = self.gw.getObject("Screen", sc_id)
            for p in scr.listChildren():
                pl_id = p.getId()
                count += 1
            assert count == 2
            assert len(ezomero.get_tag_ids(
                            self.gw, "Screen", sc_id)) == 1
