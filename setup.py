import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    packages=['', 'omero.plugins'],
    package_dir={"": "src"},
    name="omero-cli-transfer",
    version="0.0.1",
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
        'ezomero',
        'ome-types'
    ],
    python_requires='>=3.7'
)