#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
