# TWRP device tree generator

[![PyPi version](https://img.shields.io/pypi/v/twrpdtgen)](https://pypi.org/project/twrpdtgen/)
[![PyPi version status](https://img.shields.io/pypi/status/twrpdtgen)](https://pypi.org/project/twrpdtgen/)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/ded3a853b48b44b298bc3f1c95772bfd)](https://www.codacy.com/gh/SebaUbuntu/TWRP-device-tree-generator/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=SebaUbuntu/TWRP-device-tree-generator&amp;utm_campaign=Badge_Grade)

Create a [TWRP](https://twrp.me/)-compatible device tree only from an Android recovery image (or a boot image if the device uses non-dynamic partitions A/B) of your device's stock ROM
It has been confirmed that this script supports images built starting from Android 4.4 up to Android 12

## Installation

```
pip3 install twrpdtgen
```
The module is supported on Python 3.9 and above.

Linux only: Be sure to have cpio installed in your system (Install cpio using `sudo apt install cpio` or `sudo pacman -S cpio` based on what package manager you're using)

## How to use

```
$ python3 -m twrpdtgen -h
TWRP device tree generator
Version 2.1.0

usage: python3 -m twrpdtgen [-h] [-o OUTPUT] [--git] [-d] image

positional arguments:
  image                 path to an image (recovery image or boot image if the
                        device is A/B)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        custom output folder
  --git                 create a git repo after the generation
  -d, --debug           enable debugging features
```

When an image is provided, if everything goes well, there will be a device tree at `output/manufacturer/codename`

You can also use the module in a script, with the following code:

```python
from twrpdtgen.devicetree import DeviceTree

# Get image info
devicetree = DeviceTree(image_path)

# Dump device tree to folder
devicetree.dump_to_folder(output_path)
```
