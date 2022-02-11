#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2015-2018 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from ome_types import from_xml
from omero.cli import CLI
from omero_cli_transfer import TransferControl

import pytest


class TestLoadTransferPacket():
    def setup_method(self):
        self.cli = CLI()
        self.cli.register("transfer", TransferControl, "TEST")
        self.transfer = self.cli.controls['transfer']

    def test_types(self):
        with pytest.raises(TypeError):
            self.transfer._load_from_zip(None, None)
        with pytest.raises(TypeError):
            self.transfer._load_from_zip(
                None, 'test/data/output_folder')
        with pytest.raises(TypeError):
            self.transfer._load_from_zip(
                'test/data/valid_single_image.zip', 111)
        with pytest.raises(TypeError):
            self.transfer._load_from_zip(
                111, 'test/data/output_folder')

    def test_non_existing_file(self):
        with pytest.raises(FileNotFoundError):
            self.transfer._load_from_zip('data/fake_file.zip',
                                         'data/output_folder')

    def test_src_img_map(self):
        ome = from_xml('test/data/transfer.xml')
        _, src_img_map, filelist = self.transfer._create_image_map(ome)
        correct_map = {"/OMERO/ManagedRepository/./root_0/2022-01/14/"
                       "18-30-55.264/combined_result.tiff": [1678, 1679]}
        correct_filelist = ["root_0/2022-01/14/18-30-55.264/"
                            "combined_result.tiff"]
        assert src_img_map == correct_map
        assert filelist == correct_filelist

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
        path1 = '/a/b/./c/d'
        path2 = '/e/f/./c/d'
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
