# Copyright (C) 2022 The Jackson Laboratory
# Copyright (C) 2015-2018 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

import setuptools
import os

setuptools.setup(
    version=os.environ.get('VERSION', '0.0.0'),
)
