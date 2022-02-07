from __future__ import division

from omero_cli_transfer import TransferControl
from cli import CLITest


class TestTransfer(CLITest):

    def setup_method(self, method):
        super(TestTransfer, self).setup_method(method)
        self.cli.register("transfer", TransferControl, "TEST")
        self.args += ["transfer"]
        self.idonly = "-1"
        self.imageid = "Image:-1"
        self.datasetid = "Dataset:-1"
        self.projectid = "Project:-1"

    def test_extremely_naive(self):
        assert True
