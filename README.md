# TWRP device tree generator

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/69d10f044ce34de2bf7ae6ee7fe0595e)](https://app.codacy.com/manual/SebaUbuntu/TWRP-device-tree-generator?utm_source=github.com&utm_medium=referral&utm_content=SebaUbuntu/TWRP-device-tree-generator&utm_campaign=Badge_Grade_Dashboard)

Create a TWRP-compatible device tree only from a recovery.img

With this script I tried to write TwrpBuilder script in Bash, and somehow I succeded, supporing more features

## Features

-   Create device tree initial structure (like Android.mk, AndroidProduct.mk etc.)
-   Android 10 support (beta)
-   Add proper license headers in every file
-   Automatically detect device architecture
-   Pick stock recovery image info (eg. image size, kernel pagesize etc.)
-   Inherit more infos directly from the device with ADB (optional)
-   Create ad-hoc recovery.fstab
-   Add needed init.rc files
-   Take cmdline automatically
-   System-as-root support
-   dt.img support (not appended DTBs)
-   dtbo.img support (device tree blobs overlay)
-   Samsung Odin TAR support
-   Samsung SEAndroid support
-   Ramdisk compression support (LZMA, 7Z, GZIP etc...)
-   MTK support
-   Extract stock kernel automatically
-   Fill BoardConfig.mk without needing to inherit external makefiles (like TwrpBuilder does), making a standalone device tree
-   Easily improveable with a text editor, w/o needing to know any programming language
-   Create a ready-to-push git repo in device tree folder

## TODO

-   A/B support
