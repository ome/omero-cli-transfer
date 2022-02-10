from __future__ import division

from omero_cli_transfer import TransferControl
from cli import CLITest
from omero.gateway import BlitzGateway

import pytest
import os

SUPPORTED = [
    "idonly", "imageid", "datasetid", "projectid"]

TEST_FILES = [
        "test/data/valid_single_image.zip",
        "test/data/valid_single_dataset.zip",
        "test/data/valid_single_project.zip",
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

    def create_image(self, sizec=4, sizez=1, sizet=1, target_name=None):
        self.gw = BlitzGateway(client_obj=self.client)
        images = self.import_fake_file(
                images_count=2, sizeZ=sizez, sizeT=sizet, sizeC=sizec,
                client=self.client)
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

    @pytest.mark.parametrize('target_name', sorted(SUPPORTED))
    def test_non_existing_image(self, target_name, tmpdir):
        self.args += ["pack", getattr(self, target_name),
                      str(tmpdir / 'test.zip')]
        with pytest.raises(ValueError):
            self.cli.invoke(self.args, strict=True)

    @pytest.mark.parametrize('target_name', sorted(SUPPORTED))
    def test_pack(self, target_name, tmpdir):
        self.create_image(target_name=target_name)
        target = getattr(self, target_name)
        self.args += ["pack", target, str(tmpdir / 'test.zip')]
        self.cli.invoke(self.args, strict=True)
        assert os.path.exists(str(tmpdir / 'test.zip'))
        assert os.path.getsize(str(tmpdir / 'test.zip')) > 0

    @pytest.mark.parametrize('package_name', sorted(TEST_FILES))
    def test_unpack(self, package_name):
        self.args += ["unpack", package_name]
        self.cli.invoke(self.args, strict=True)
