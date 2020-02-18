# TWRP device tree generator

Create a TWRP-compatible device tree only from a recovery.img

With this script I tried to write TwrpBuilder script in Bash, and somehow I succeded (even thought it doesn't do all TwrpBuilder script does, it's still WIP)

## Features

- Create device tree initial structure (like Android.mk, AndroidProduct.mk etc.)
- Add proper license headers in every file
- Automatically detect device architecture
- Pick stock recovery image info (eg. image size, kernel pagesize etc.)
- Create ad-hoc recovery.fstab
- Add needed init.rc files
- MTK support
- Extract stock kernel automatically
- Fill BoardConfig.mk without needing to inherit external makefiles (like TwrpBuilder does), making a standalone device tree
- Easily improveable with a text editor, w/o needing to know any programming language
- Create a ready-to-push git repo in device tree folder

## TODO

- Inherit more infos directly from the device with ADB
