# Copyright (C) 2023 The Jackson Laboratory
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

from omero_cli_transfer import TransferControl
from cli import CLITest
from omero.gateway import BlitzGateway

# import ezomero
import pytest
# import os
# import tarfile
import json
from pathlib import Path

import logging

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SUPPORTED = [
    "idonly", "imageid", "datasetid", "projectid"]


class TestFigure(CLITest):

    def setup_method(self, method):
        super(TestFigure, self).setup_method(method)
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
            logger.info(f"deleting project {pj_id}")
            self.gw.deleteObjects("Project", [pj_id], deleteAnns=True,
                                  deleteChildren=True, wait=True)
        ds = self.gw.getObjects("Dataset")
        for d in ds:
            ds_id = d.id
            logger.info(f"deleting dataset {ds_id}")
            self.gw.deleteObjects("Dataset", [ds_id], deleteAnns=True,
                                  deleteChildren=True, wait=True)
        scs = self.gw.getObjects("Screen")
        for sc in scs:
            sc_id = sc.id
            logger.info(f"deleting screen {sc_id}")
            self.gw.deleteObjects("Screen", [sc_id], deleteAnns=True,
                                  deleteChildren=True, wait=True)
        pls = self.gw.getObjects("Plate")
        for pl in pls:
            pl_id = pl.id
            logger.info(f"deleting plate {pl_id}")
            self.gw.deleteObjects("Plate", [pl_id], deleteAnns=True,
                                  deleteChildren=True, wait=True)
        ims = self.gw.getObjects("Image")
        im_ids = []
        for im in ims:
            im_ids.append(im.id)
            logger.info(f"deleting image {im.id}")
        if im_ids:
            self.gw.deleteObjects("Image", im_ids, deleteAnns=True,
                                  deleteChildren=True, wait=True)
        fas = self.gw.getObjects("FileAnnotation")
        fa_ids = []
        for fa in fas:
            fa_ids.append(fa.id)
            logger.info(f"deleting file annotation {fa.id}")
        if fa_ids:
            self.gw.deleteObjects("FileAnnotation", fa_ids,
                                  deleteChildren=True, wait=True)

    def get_panel_json(self, image, index, page_x):
        """Create a panel."""
        channel = {'emissionWave': "400",
                   'label': "DAPI",
                   'color': "0000FF",
                   'inverted': False,
                   'active': True,
                   'window': {'min': 0,
                              'max': 255,
                              'start': 0,
                              'end': 255},
                   }
        img = self.gw.getObject("Image", image)
        pix = img.getPrimaryPixels()
        size_x = pix.getSizeX()
        size_y = pix.getSizeY()
        # shapes coordinates are Image coordinates
        # Red Line diagonal from corner to corner
        # Arrow from other corner to centre
        shapes = [
            {"type": "Rectangle", "x": size_x/4, "y": size_y/4,
             "width": size_x/2, "height": size_y/2,
             "strokeWidth": 4, "strokeColor": "#FFFFFF"},
            {"type": "Line", "x1": 0, "x2": size_x, "y1": 0,
             "y2": size_y, "strokeWidth": 5, "strokeColor": "#FF0000"},
            {"type": "Arrow", "x1": 0, "x2": size_x/2, "y1": size_y,
             "y2": size_y/2, "strokeWidth": 10, "strokeColor": "#FFFF00"},
            {"type": "Ellipse", "x": size_x/2, "y": size_y/2,
             "radiusX": size_x/3, "radiusY": size_y/2, "rotation": 45,
             "strokeWidth": 10, "strokeColor": "#00FF00"}]

        # This works if we have Units support (OMERO 5.1)
        px = pix.getPhysicalSizeX()
        py = pix.getPhysicalSizeY()
        pz = pix.getPhysicalSizeZ()
        img_json = {
            "imageId": image,
            "name": "test_image",  # image.getName().getValue()
            "width": 100 * (index + 1),
            "height": 100 * (index + 1),
            "sizeZ": pix.getSizeZ(),
            "theZ": 0,
            "sizeT": pix.getSizeT(),
            "theT": 0,
            # rdef -> used at panel creation then deleted
            "channels": [channel],
            "orig_width": size_x,
            "orig_height": size_y,
            "x": page_x,
            "y": index * 200,
            'datasetName': "TestDataset",
            'datasetId': 123,
            'pixel_size_x': None if px is None else px.getValue(),
            'pixel_size_y': None if py is None else py.getValue(),
            'pixel_size_z': None if pz is None else pz.getValue(),
            'pixel_size_x_symbol': '\xB5m' if px is None else px.getSymbol(),
            'pixel_size_z_symbol': None if pz is None else pz.getSymbol(),
            'pixel_size_x_unit': None if px is None else str(px.getUnit()),
            'pixel_size_z_unit': None if pz is None else str(pz.getUnit()),
            'deltaT': [],
            "zoom": 100 + (index * 50),
            "dx": 0,
            "dy": 0,
            "rotation": 100 * index,
            "rotation_symbol": '\xB0',
            "max_export_dpi": 1000,
            "shapes": shapes,
        }
        return img_json

    def create_figure(self, image_ids):
        """Create JSON to export figure."""
        figure_json = {"version": 2,
                       "paper_width": 595,
                       "paper_height": 842,
                       "page_size": "A4",
                       }
        panels = []
        idx = 0
        for image in image_ids:
            panels.append(self.get_panel_json(image, 0, 50 + (idx * 300)))
            panels.append(self.get_panel_json(image, 1, 50 + (idx * 300)))
            idx += 1
        figure_json['panels'] = panels
        json_string = json.dumps(figure_json)
        return json_string

    @pytest.mark.parametrize('target_name', sorted(SUPPORTED))
    def test_pack_unpack_figure(self, target_name, tmpdir):

        # basic case
        self.create_image(target_name=target_name)
        clear_img_id = int(self.imageid.split(":")[-1])
        jsonstr = self.create_figure([clear_img_id])
        logger.info(jsonstr)
        with open(Path(tmpdir)/"figure.json", 'w') as f:
            f.write(jsonstr)
        # ezomero cannot create orphaned FileAnnotations...
        namespace = "omero.web.figure.json"
        self.gw.createFileAnnfromLocalFile(
            str(Path(tmpdir)/"figure.json"),
            mimetype="application/json",
            ns=namespace, desc=None)
        target = getattr(self, target_name)
        args = self.args + ["pack", target, '--figure',
                            str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        self.delete_all()
        args = self.args + ["unpack", '--figure',
                            str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        fas = self.gw.getObjects("FileAnnotation")
        count = 0
        for f in fas:
            count += 1
        assert count == 1
        self.delete_all()

        # figure w/multi-images, one in, one out
        self.create_image(target_name=target_name)
        clear_img_id = int(self.imageid.split(":")[-1])
        other_img = int(self.create_test_image(100, 100, 1, 1, 1,
                        self.client.getSession()).id.val)
        logger.info(clear_img_id, other_img)
        jsonstr = self.create_figure([clear_img_id, other_img])
        logger.info(jsonstr)
        with open(Path(tmpdir)/"figure.json", 'w') as f:
            f.write(jsonstr)
        # ezomero cannot create orphaned FileAnnotations...
        namespace = "omero.web.figure.json"
        self.gw.createFileAnnfromLocalFile(
            str(Path(tmpdir)/"figure.json"),
            mimetype="application/json",
            ns=namespace, desc=None)
        target = getattr(self, target_name)
        args = self.args + ["pack", target, '--figure',
                            str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        self.delete_all()
        args = self.args + ["unpack", '--figure',
                            str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        fas = self.gw.getObjects("FileAnnotation")
        count = 0
        for f in fas:
            count += 1
        assert count == 1
        self.delete_all()

        # figure w/multi-images, two in, one out
        self.create_image(target_name=target_name)
        clear_img_id = int(self.imageid.split(":")[-1])
        clear_src_id = int(self.source.split(":")[-1])
        other_img = int(self.create_test_image(100, 100, 1, 1, 1,
                        self.client.getSession()).id.val)
        logger.info(clear_img_id, other_img)
        jsonstr = self.create_figure([clear_img_id, other_img, clear_src_id])
        logger.info(jsonstr)
        with open(Path(tmpdir)/"figure.json", 'w') as f:
            f.write(jsonstr)
        namespace = "omero.web.figure.json"
        self.gw.createFileAnnfromLocalFile(
            str(Path(tmpdir)/"figure.json"),
            mimetype="application/json",
            ns=namespace, desc=None)
        # create another figure with source only
        jsonstr = self.create_figure([other_img, clear_src_id])
        logger.info(jsonstr)
        with open(Path(tmpdir)/"figure.json", 'w') as f:
            f.write(jsonstr)
        # ezomero cannot create orphaned FileAnnotations...
        namespace = "omero.web.figure.json"
        self.gw.createFileAnnfromLocalFile(
            str(Path(tmpdir)/"figure.json"),
            mimetype="application/json",
            ns=namespace, desc=None)
        target = getattr(self, target_name)
        args = self.args + ["pack", target, '--figure',
                            str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        self.delete_all()
        args = self.args + ["unpack", '--figure',
                            str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        fas = self.gw.getObjects("FileAnnotation")
        count = 0
        for f in fas:
            count += 1
        if target == "imageid":
            assert count == 1
        else:
            assert count == 2
        self.delete_all()

        # figure without relevant images
        self.create_image(target_name=target_name)
        other_img1 = int(self.create_test_image(100, 100, 1, 1, 1,
                         self.client.getSession()).id.val)
        other_img2 = int(self.create_test_image(100, 100, 1, 1, 1,
                         self.client.getSession()).id.val)
        logger.info(clear_img_id, other_img)
        jsonstr = self.create_figure([other_img1, other_img2])
        logger.info(jsonstr)
        with open(Path(tmpdir)/"figure.json", 'w') as f:
            f.write(jsonstr)
        namespace = "omero.web.figure.json"
        self.gw.createFileAnnfromLocalFile(
            str(Path(tmpdir)/"figure.json"),
            mimetype="application/json",
            ns=namespace, desc=None)
        target = getattr(self, target_name)
        args = self.args + ["pack", target, '--figure',
                            str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        self.delete_all()
        args = self.args + ["unpack", '--figure',
                            str(tmpdir / 'test.tar')]
        self.cli.invoke(args, strict=True)
        fas = self.gw.getObjects("FileAnnotation")
        count = 0
        for f in fas:
            count += 1
        assert count == 0
        self.delete_all()
