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

The syntax for specifying objects is: <object>:<id> where <object> can be Image, Project or Dataset. Project is assumed if <object>: is omitted. A file path needs to be provided; a tar file with the contents of the packet will be created at the specified path.

Currently, only MapAnnotations, Tags, FileAnnotations and CommentAnnotations are packaged into the transfer pack, and only Point, Line, Ellipse, Rectangle and Polygon-type ROIs are packaged.

`--zip` packs the object into a compressed zip file rather than a tarball.

`--barchive` creates a package compliant with Bioimage Archive submission standards - see below for more detail.

Examples:
```
omero transfer pack Image:123 transfer_pack.tar
omero transfer pack --zip Image:123 transfer_pack.zip
omero transfer pack Dataset:1111 /home/user/new_folder/new_pack.tar
omero transfer pack 999 tarfile.tar  # equivalent to Project:999
```

## `omero transfer unpack`

Unpacks an existing transfer packet, imports images as orphans and uses the XML contained in the transfer packet to re-create links, annotations and ROIs.

`--ln_s` forces imports to use the transfer=ln_s option, in-place importing files. Same restrictions of regular in-place imports apply.

`--output` allows for specifying an optional output folder where the packet will be unzipped.

`--folder` allows the user to point to a previously-unpacked folder rather than a single file.

Examples:
```
omero transfer unpack transfer_pack.zip
omero transfer unpack --output /home/user/optional_folder --ln_s
omero transfer unpack --folder /home/user/unpacked_folder/
```

### Bioimage Archive submission contents

- Folder structure in the generated zip/tar follows project/dataset structure rather than original ManagedRepository folder structure, and instead of a `transfer.xml` file, a `submission.tsv` file is generated.
- `submission.tsv` file has:

    - one line per file being submitted, between `Image` files and `FileAnnotation` files;
    - a column indicating whether that file was originally an `Image` or `FileAnnotation`;
    - a "comment" column if any Image has a `CommentAnnotation`;
    - a column per key in a `MapAnnotation` inside the pack, with an empty value for all images but the ones with a `MapAnnotation` with that key; for those images, it has the value for that annotation;
    - a final `original_omero_ids` column listing all OMERO IDs associated to that file in the origin server: for images, that is all `Image` IDs that use that file, and for file annotations that is all `Image` IDs that had that `FileAnnotation` attached to them.
