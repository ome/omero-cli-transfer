# omero-cli-transfer
An OMERO CLI plugin for creating and using transfer packets between OMERO servers.

Transfer packets contain objects and annotations. This project creates a zip file from an object 
(Project, Dataset, Image, Screen, Plate) containing all original files necessary to create the images 
in that object, plus an XML file detailing the links between entities, annotations and ROIs thereof.

The CLI plugin add the subcommand `transfer`, which in its turn has two further subcommands `omero transfer pack` and `omero transfer unpack`. Both subcommands (pack and unpack) will use an existing OMERO session created via CLI or prompt the user for parameters to create one.

# Installation
tl;dr: if you have `python>=3.7`, a simple `pip install omero-cli-transfer` _might_ do. We recommend conda, though.

`omero-cli-transfer` requires at least Python 3.7. This is due to `ome-types` requiring that as well;
this package relies heavily on it, and it is not feasible without it. 

Of course, this CAN be an issue, especially given `omero-py` _officially_ only supports Python 3.6. However,
it is possible to run `omero-py` in Python 3.7 or newer as well. Our recommended way to do so it using `conda`.
With conda installed, you can do
```
conda create -n myenv -c ome python=3.7 zeroc-ice36-python
conda activate myenv
pip install omero-cli-transfer
```
It is possible to do the same thing without `conda` as long as your python/pip version is at least 3.7,
but that will require locally building a wheel for `zeroc-ice` (which pip does automatically) - it is a
process that can be anything from "completely seamless and without issues" to "I need to install every 
dependency ever imagined". Try at your own risk.

# Usage

## `omero transfer pack`

Creates a transfer packet for moving objects between OMERO server instances.

The syntax for specifying objects is: `object`:`id` where `object` can be Image, Project, Dataset, Screen or Plate. 
Project is assumed if `object:` is omitted.
A file path needs to be provided; a zip file with the contents of the packet will be created at the specified path.

Types of annotations packaged: MapAnnotations, Tags, CommentAnnotations, FileAnnotations, LongAnnotations (ratings).
Types of ROIs packaged: Point, Line, Ellipse, Rectangle, Polygon, Polyline, Label, Arrow.

Examples:
```
omero transfer pack Image:123 transfer_pack.zip
omero transfer pack Dataset:1111 /home/user/new_folder/new_pack.zip
omero transfer pack 999 zipfile.zip  # equivalent to Project:999
```

## `omero transfer unpack`

Unpacks an existing transfer packet, imports images/plates as orphans and uses the XML contained in the transfer packet to re-create links, annotations and ROIs.

`--ln_s` forces imports to use the transfer=ln_s option, in-place importing files. Same restrictions of regular in-place imports apply.

`--output` allows for specifying an optional output folder where the packet will be unzipped. 

Examples:
```
omero transfer unpack transfer_pack.zip
omero transfer unpack --output /home/user/optional_folder --ln_s
```