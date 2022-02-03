# omero-cli-transfer
An OMERO CLI plugin for creating and using transfer packets between OMERO servers.

Transfer packets contain objects and annotations. This project creates a zip file from an object (Project/Dataset/Image) containing all original files necessary to create the images in that object, plus an XML file detailing the links between entities, annotations and ROIs thereof.

The CLI plugin add the subcommand `transfer`, which in its turn has two further subcommands `omero transfer pack` and `omero transfer unpack`. Both subcommands (pack and unpack) will use an existing OMERO session created via CLI or prompt the user for parameters to create one.

## `omero transfer pack`

Creates a transfer packet for moving objects between OMERO server instances.

The syntax for specifying objects is: `object`:`id` where `object` can be Image, Project or Dataset. Project is assumed if `object:` is omitted.
A file path needs to be provided; a zip file with the contents of the packet will be created at the specified path.

Currently, only MapAnnotations and Tags are packaged into the transfer pack, and only Point, Line, Ellipse, Rectangle and Polygon-type ROIs are packaged.

Examples:
```
omero transfer pack Image:123 transfer_pack.zip
omero transfer pack Dataset:1111 /home/user/new_folder/new_pack.zip
omero transfer pack 999 zipfile.zip  # equivalent to Project:999
```

## `omero transfer unpack`

Unpacks an existing transfer packet, imports images as orphans and uses the XML contained in the transfer packet to re-create links, annotations and ROIs.

`--ln_s` forces imports to use the transfer=ln_s option, in-place importing files. Same restrictions of regular in-place imports apply.

`--output` allows for specifying an optional output folder where the packet will be unzipped. 

Examples:
```
omero transfer unpack transfer_pack.zip
omero transfer unpack --output /home/user/optional_folder --ln_s
```