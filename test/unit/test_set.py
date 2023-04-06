#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 The Jackson Laboratory
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

from ome_types import from_xml
from omero.cli import CLI
from omero.gateway import BlitzGateway
from omero_cli_transfer import TransferControl

import pytest


class TestPackSide():
    def setup_method(self):
        self.cli = CLI()
        self.cli.register("transfer", TransferControl, "TEST")
        self.transfer = self.cli.controls['transfer']

    def test_copy_files_inputs(self):
        conn = BlitzGateway()
        with pytest.raises(TypeError):
            self.transfer._copy_files(12, "test_folder", conn)
        with pytest.raises(TypeError):
            self.transfer._copy_files([12], "test_folder", conn)
        with pytest.raises(TypeError):
            self.transfer._copy_files({'Image:12': 'test'}, 12, conn)
        with pytest.raises(TypeError):
            self.transfer._copy_files({'Image:12': 'test'}, "test_folder", 12)

    def test_process_metadata(self):
        metadata = None
        self.transfer._process_metadata(metadata)
        assert set(self.transfer.metadata) == \
            set(["img_id", "plate_id", "timestamp", "software", "version",
                 "hostname", "md5", "orig_user", "orig_group"])
        self.transfer.metadata = []
        metadata = ['all', 'db_id']
        self.transfer._process_metadata(metadata)
        assert set(self.transfer.metadata) == \
            set(["img_id", "plate_id", "timestamp", "software", "version",
                 "hostname", "md5", "orig_user", "orig_group", "db_id"])
        self.transfer.metadata = []
        metadata = ['none', 'db_id']
        self.transfer._process_metadata(metadata)
        assert self.transfer.metadata is None
        self.transfer.metadata = []
        metadata = ["timestamp", "software", "version"]
        self.transfer._process_metadata(metadata)
        assert set(self.transfer.metadata) == \
            set(["timestamp", "software", "version"])


class TestUnpackSide():
    def setup_method(self):
        self.cli = CLI()
        self.cli.register("transfer", TransferControl, "TEST")
        self.transfer = self.cli.controls['transfer']

    def test_load_pack(self):
        with pytest.raises(TypeError):
            self.transfer._load_from_pack(None, None)
        with pytest.raises(TypeError):
            self.transfer._load_from_pack(
                None, 'test/data/output_folder')
        with pytest.raises(TypeError):
            self.transfer._load_from_pack(
                'test/data/valid_single_image.zip', 111)
        with pytest.raises(TypeError):
            self.transfer._load_from_pack(
                111, 'test/data/output_folder')
        hash, ome, folder = self.transfer._load_from_pack(
            "test/data/valid_single_image.zip", "tmp_folder")
        assert hash == "ac050c218f01bf189f9b3bdc9cab4f37"
        assert len(ome.images) == 1
        assert str(folder.resolve()) == "/omero-cli-transfer/tmp_folder"
        hash, ome, folder = self.transfer._load_from_pack(
            "test/data/valid_single_image.zip")
        assert str(folder.resolve()) == \
            "/omero-cli-transfer/test/data/valid_single_image"

    def test_non_existing_file(self):
        with pytest.raises(FileNotFoundError):
            self.transfer._load_from_pack('data/fake_file.zip',
                                          'data/output_folder')

    def test_src_img_map(self):
        ome = from_xml('test/data/transfer.xml')
        _, src_img_map, filelist = self.transfer._create_image_map(ome)
        correct_map = {"root_0/2022-01/14/"
                       "18-30-55.264/combined_result.tiff": [1678, 1679]}
        correct_filelist = ["root_0/2022-01/14/18-30-55.264/"
                            "combined_result.tiff"]
        assert src_img_map == correct_map
        assert filelist == correct_filelist
        ome = None
        with pytest.raises(TypeError):
            _, src_img_map, filelist = self.transfer._create_image_map(ome)

    def test_import(self):
        # well I don't know how to do this since stdin is not a terminal
        # gateway = ezomero.connect(host='localhost', port=4064,
        #                           user='root', password='omero',
        #                           secure=True, group='')
        # folder = 'test/data'
        # filelist = ['test_pyramid.ome.tif']
        # ln_s = False
        # img_map = self.transfer._import_files(folder, filelist, ln_s,
        #                                       gateway)
        # assert len(img_map.keys()) == 1
        # assert str(os.path.join(folder, '.', filelist[0])) in img_map.keys()
        # assert isinstance(img_map[str(os.path.join(folder, '.',
        #                   filelist[0]))], int)
        assert True

    def test_image_map(self):
        path1 = 'c/d'
        path2 = 'c/d'
        src_map = {path1: [1]}
        dest_map = {path2: [2]}
        imgmap = self.transfer._make_image_map(src_map, dest_map)
        assert len(imgmap.keys()) == 1
        assert f"Image:{src_map[path1][0]}" in imgmap.keys()
        assert imgmap[f"Image:{src_map[path1][0]}"] == 2

        src_map = {path1: [1, 2, 3, 4]}
        dest_map = {path2: [2, 7, 9, 14]}
        imgmap = self.transfer._make_image_map(src_map, dest_map)
        assert len(imgmap.keys()) == 4
        assert f"Image:{src_map[path1][0]}" in imgmap.keys()
        assert imgmap[f"Image:{src_map[path1][0]}"] == 2
        assert imgmap[f"Image:{src_map[path1][1]}"] == 7
        assert imgmap[f"Image:{src_map[path1][2]}"] == 9
        assert imgmap[f"Image:{src_map[path1][3]}"] == 14

        path2 = '/e/f/c/d'
        dest_map = {path2: [2, 7, 9, 14]}
        imgmap = self.transfer._make_image_map(src_map, dest_map)
        assert imgmap == {}
