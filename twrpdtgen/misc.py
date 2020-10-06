#!/usr/bin/python

from itertools import repeat
from pathlib import Path
from stat import S_IWRITE
from typing import Optional

from twrpdtgen import jinja_env


def render_template(device_tree_path: Optional[Path], template_file: str,
                    out_file: str = '', to_file=True, **kwargs):
    template = jinja_env.get_template(template_file)
    rendered_template = template.render(**kwargs)
    if to_file:
        if not out_file:
            out_file = template_file.replace('.jinja2', '')
        with open(f"{device_tree_path}/{out_file}", 'w', encoding="utf-8") as out:
            out.write(rendered_template)
        return True
    else:
        return rendered_template


def error(err):
    print("Error:", err)


def make_twrp_fstab(old_fstab, new_fstab):
    orig_fstab = open(old_fstab)
    dest_fstab = open(new_fstab, "w")
    fstab_entries = orig_fstab.read()
    fstab_entries = fstab_entries.splitlines()
    default_name_fs_space = 19
    default_fs_path_space = 9
    default_path_flags_space = 69
    partition_path_location = 0
    partition_name_location = 1
    partition_fs_location = 2
    allowed_partitions = {
        # Boot partitions
        "/boot": True,
        "/recovery": True,
        "/dtbo": True,

        # Standard partitions
        "/cache": True,
        "/data": True,
        "/odm": True,
        "/product": True,
        "/system": True,
        "/vendor": True,

        # OEM partitions
        "/cust": True,
        "/firmware": True,
        "/persist": True,

        # Logical partitions
        "system": True,
        "odm": True,
        "product": True,
        "vendor": True
    }
    partition_needs_image_entry = {
        "/odm": True,
        "/product": True,
        "/system": True,
        "/vendor": True,
        "/persist": True
    }
    partition_flags = {
        "/recovery": 'flags=backup=1',
        "/dtbo": 'flags=display="Dtbo";backup=1;flashimg=1',
        "/odm": 'flags=display="Odm";backup=1',
        "/product": 'flags=display="Product";backup=1',
        "/system": 'flags=backup=1',
        "/vendor": 'flags=display="Vendor";backup=1',
        "/cust": 'flags=display="Cust"',
        "/firmware": 'flags=display="Firmware"',
        "/persist": 'flags=display="Persist"',
        "system": 'flags=display="System";logical',
        "odm": 'flags=display="Odm";logical',
        "product": 'flags=display="Product";logical',
        "vendor": 'flags=display="Vendor";logical',
        "/odm_image": 'flags=display="Odm image";backup=1;flashimg=1',
        "/product_image": 'flags=display="Product image";backup=1;flashimg=1',
        "/system_image": 'flags=display="System image";backup=1;flashimg=1',
        "/vendor_image": 'flags=display="Vendor image";backup=1;flashimg=1',
        "/persist_image": 'flags=display="Persist image";backup=1;flashimg=1'
    }
    partition_alternative_name = {
        "/": "/system",
        "/system_root": "/system"
    }
    dest_fstab.write("# Android fstab file." + "\n")
    dest_fstab.write("# The filesystem that contains the filesystem checker binary (typically /system) cannot" + "\n")
    dest_fstab.write("# specify MF_CHECK, and must come before any filesystems that do specify MF_CHECK" + "\n")
    dest_fstab.write("\n")
    dest_fstab.write(
        "# mount point       fstype    device                                                                flags" + "\n")
    for entry in fstab_entries:
        split_entry = entry.split()
        if not entry.startswith("#") and len(split_entry) >= 2:
            if split_entry[1] in ["emmc", "ext4", "f2fs", "vfat", "auto"]:
                partition_name_location = 0
                partition_fs_location = 1
                partition_path_location = 2
            partition_path = split_entry[partition_path_location]
            partition_name = split_entry[partition_name_location]
            partition_fs = split_entry[partition_fs_location]
            partition_name = partition_alternative_name.get(partition_name, partition_name)
            if allowed_partitions.get(partition_name, False):
                name_fs_space_int = default_name_fs_space - len(partition_name)
                fs_path_space_int = default_fs_path_space - len(partition_fs)
                path_flags_space_int = default_path_flags_space - len(partition_path)
                name_fs_space = " "
                fs_path_space = " "
                path_flags_space = " "
                for _ in repeat(None, name_fs_space_int):
                    name_fs_space += " "
                for _ in repeat(None, fs_path_space_int):
                    fs_path_space += " "
                for _ in repeat(None, path_flags_space_int):
                    path_flags_space += " "
                dest_fstab.write(
                    partition_name + name_fs_space + partition_fs + fs_path_space + partition_path + path_flags_space + partition_flags.get(
                        partition_name, "") + "\n")
                if partition_needs_image_entry.get(partition_name, False):
                    name_fs_space_int = default_name_fs_space - len(partition_name + "_image")
                    name_fs_space = " "
                    for _ in repeat(None, name_fs_space_int):
                        name_fs_space += " "
                    dest_fstab.write(
                        partition_name + "_image" + name_fs_space + "emmc" + fs_path_space + partition_path + path_flags_space + partition_flags.get(
                            partition_name + "_image", "") + "\n")
    orig_fstab.close()
    dest_fstab.close()


def print_help():
    print("Usage: start.py <recovery image path>")


def handle_remove_readonly(func, path, _):
    Path(path).chmod(S_IWRITE)
    func(path)
