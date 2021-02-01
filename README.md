# TWRP device tree generator

[![PyPi version](https://img.shields.io/pypi/v/twrpdtgen)](https://pypi.org/project/twrpdtgen/)
[![PyPi version status](https://img.shields.io/pypi/status/twrpdtgen)](https://pypi.org/project/twrpdtgen/)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/ded3a853b48b44b298bc3f1c95772bfd)](https://www.codacy.com/gh/SebaUbuntu/TWRP-device-tree-generator/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=SebaUbuntu/TWRP-device-tree-generator&amp;utm_campaign=Badge_Grade)

Create a [TWRP](https://twrp.me/)-compatible device tree only from an Android recovery image (or a boot image if the device uses non-dynamic partitions A/B) of your device's stock ROM
It has been confirmed that this script supports images built starting from Android 4.4 up to Android 11

## Installation

```
pip3 install twrpdtgen
```
The module is supported on Python 3.6 and above.

Linux only: Be sure to have cpio installed in your system (Install cpio using `sudo apt install cpio` or `sudo pacman -S cpio` based on what package manager you're using)

## How to use

```
$ python3 -m twrpdtgen -h
TWRP device tree generator

usage: python3 -m twrpdtgen [-h] [-o OUTPUT] [-k] [--no-git] [--huawei] [--recovery_kernel RECOVERY_KERNEL] [--recovery_ramdisk RECOVERY_RAMDISK]
                            [--recovery_vendor RECOVERY_VENDOR] [-v]
                            [recovery_image]

positional arguments:
  recovery_image        path to a recovery image (or boot image if the device is A/B)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        custom output folder
  -k, --keep-aik        keep AIK after the generation
  --no-git              don't create a git repo after the generation
  --huawei              Huawei mode (split kernel, ramdisk and vendor)
  --recovery_kernel RECOVERY_KERNEL
                        path to a recovery_kernel file (huawei mode only)
  --recovery_ramdisk RECOVERY_RAMDISK
                        path to a recovery_ramdisk file (huawei mode only)
  --recovery_vendor RECOVERY_VENDOR
                        path to a recovery_vendor file (huawei mode only)
  -v, --verbose         enable debugging logging
```

When an image is provided, if everything goes well, there will be a device tree at `output/manufacturer/codename`

You can also use the module in a script, with the following code:

```python
from twrpdtgen.twrp_dt_gen import generate_device_tree

# The function will return a DeviceTree object, you can find its declaration here:
from twrpdtgen.utils.device_tree import DeviceTree

result = generate_device_tree(image_path, output_path)

```
