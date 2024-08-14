# Copyright (C) 2022 The Jackson Laboratory
# Copyright (C) 2015-2018 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# Use is subject to license terms supplied in LICENSE.

import os
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


def read(fname):
    """
    Utility function to read the README file.
    :rtype : String
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    packages=['', 'omero.plugins'],
    package_dir={"": "src"},
    name="omero-cli-transfer",
    version='1.1.0',
    maintainer="Erick Ratamero",
    maintainer_email="erick.ratamero@jax.org",
    description=("A set of utilities for exporting a transfer"
                 " packet from an OMERO server and importing "
                 "it in a different server. Developed by the "
                 "Research IT team at The Jackson Laboratory."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TheJacksonLaboratory/omero-cli-transfer",
    install_requires=[
        'ezomero>=2.1.0, <3.0.0',
        'ome-types==0.5.1.post1'
    ],
    extras_require={
        "rocrate": ["rocrate==0.7.0"],
    },
    python_requires='>=3.8',

)
