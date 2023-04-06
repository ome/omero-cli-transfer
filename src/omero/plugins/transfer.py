#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2022 The Jackson Laboratory
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

"""
   Plugin for transfering objects and annotations between servers

"""

from omero_cli_transfer import TransferControl, HELP
from omero.cli import CLI
import sys

try:
    register("transfer", TransferControl, HELP)
except NameError:
    if __name__ == "__main__":
        cli = CLI()
        cli.register("transfer", TransferControl, HELP)
        cli.invoke(sys.argv[1:])
