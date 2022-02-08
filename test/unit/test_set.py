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
                'data/valid_single_image.zip', None)
        with pytest.raises(TypeError):
            self.transfer._load_from_zip(
                None, 'data/output_folder')
        with pytest.raises(TypeError):
            self.transfer._load_from_zip(
                'data/valid_single_image.zip', 111)
        with pytest.raises(TypeError):
            self.transfer._load_from_zip(
                111, 'data/output_folder')

    def test_non_existing_file(self):
        with pytest.raises(FileNotFoundError):
            self.transfer._load_from_zip('data/fake_file.zip',
                                         'data/output_folder')

#     def test_no_channels(self, tmpdir):
#         d = {'version': 1}
#         f = write_yaml(d, tmpdir)
#         with pytest.raises(NonZeroReturnCode) as e:
#             self.render._load_rendering_settings(f)
#         assert e.value.rv == 104

#     def test_missing_version_pass(self, tmpdir):
#         d = {'channels': {1: {'label': 'foo'}}}
#         f = write_yaml(d, tmpdir)
#         data = self.render._load_rendering_settings(f)
#         assert data == d
#         assert _getversion(d) == SPEC_VERSION

#     @pytest.mark.parametrize('key1', ['start', 'end'])
#     @pytest.mark.parametrize('key2', ['min', 'max'])
#     def test_missing_version_fail(self, tmpdir, key1, key2):
#         d = {'channels': {1: {key1: 100, key2: 200}}}
#         f = write_yaml(d, tmpdir)
#         with pytest.raises(NonZeroReturnCode) as e:
#             self.render._load_rendering_settings(f)
#         assert e.value.rv == 124

#     @pytest.mark.parametrize('key', ['start', 'end'])
#     def test_version_2(self, tmpdir, key):
#         d = {'channels': {1: {key: 100, 'label': 'foo'}}}
#         f = write_yaml(d, tmpdir)
#         data = self.render._load_rendering_settings(f)
#         assert data == d
#         assert _getversion(d) == 2

#     @pytest.mark.parametrize('key', ['min', 'max'])
#     def test_version_1(self, tmpdir, key):
#         d = {'channels': {1: {key: 100, 'label': 'foo'}}}
#         f = write_yaml(d, tmpdir)
#         data = self.render._load_rendering_settings(f)
#         assert data == d
#         assert _getversion(d) == 1

#     @pytest.mark.parametrize('version', [1, 2])
#     def test_version_detection(self, tmpdir, version):
#         d = {'version': version, 'channels': {1: {'label': 'foo'}}}
#         f = write_yaml(d, tmpdir)
#         data = self.render._load_rendering_settings(f)
#         assert data == d
#         assert _getversion(d) == version

#     def test_version_fail(self, tmpdir):
#         d = {'version': 0, 'channels': {1: {'label': 'foo'}}}
#         f = write_yaml(d, tmpdir)
#         with pytest.raises(NonZeroReturnCode) as e:
#             self.render._load_rendering_settings(f)
#         assert e.value.rv == 124


# class TestReadChannels:
#     def setup_method(self):
#         self.cli = CLI()
#         self.cli.register("render", RenderControl, "TEST")
#         self.render = self.cli.controls['render']

#     def test_non_integer_channel(self):
#         d = {'channels': {'GFP': {'label': 'foo'}}}
#         with pytest.raises(NonZeroReturnCode) as e:
#             self.render._read_channels(d)
#         assert e.value.rv == 105

#     @pytest.mark.parametrize('key', ['min', 'max', 'start', 'end'])
#     def test_float_keys(self, key):
#         d = {'channels': {1: {key: 'foo'}}}
#         with pytest.raises(NonZeroReturnCode) as e:
#             self.render._read_channels(d)
#         assert e.value.rv == 105
