#!/usr/bin/python

import datetime
import itertools
import magic

def append_license(target, year, comment):
	current_year = str(datetime.datetime.now().year)
	file = open(target, "w")
	file.write(comment + "\n")
	file.write(comment + " " + 'Copyright (C)' + " " + year + " " + 'The Android Open Source Project' + "\n")
	file.write(comment + " " + 'Copyright (C)' + " " + year + " " + 'The TWRP Open Source Project' + "\n")
	file.write(comment + " " + 'Copyright (C)' + " " + current_year + " " + "SebaUbuntu's TWRP device tree generator" + "\n")
	file.write(comment + "\n")
	file.write(comment + " " + 'Licensed under the Apache License, Version 2.0 (the "License");' + "\n")
	file.write(comment + " " + 'you may not use this file except in compliance with the License.' + "\n")
	file.write(comment + " " + 'You may obtain a copy of the License at' + "\n")
	file.write(comment + "\n")
	file.write(comment + " " + '    http://www.apache.org/licenses/LICENSE-2.0' + "\n")
	file.write(comment + "\n")
	file.write(comment + " " + 'Unless required by applicable law or agreed to in writing, software' + "\n")
	file.write(comment + " " + 'distributed under the License is distributed on an "AS IS" BASIS,' + "\n")
	file.write(comment + " " + 'WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.' + "\n")
	file.write(comment + " " + 'See the License for the specific language governing permissions and' + "\n")
	file.write(comment + " " + 'limitations under the License.' + "\n")
	file.write(comment + "\n")
	file.write("\n")
	file.close()

def error(error):
	print("Error:", error)

def get_device_arch(binary):
	bin_magic = magic.from_file(str(binary))
	if "ARM" in bin_magic:
		if "aarch64" in bin_magic:
			return "arm64"
		else:
			return "arm"
	elif "x86" in bin_magic:
		if "aarch64" in bin_magic:
			return "x86_64"
		else:
			return "x86"
	else:
		return False

def make_twrp_fstab(old_fstab, new_fstab):
	orig_fstab = open(old_fstab)
	dest_fstab = open(new_fstab, "w")
	fstab_entries = orig_fstab.read()
	fstab_entries = fstab_entries.splitlines()
	default_name_fs_space = 19
	default_fs_path_space = 9
	default_path_flags_space = 69
	allowed_partitions = {
		# Boot partitions
		"/boot": True,
		"/recovery": True,
		"/dtbo": True,

		# Standard partitions
		"/cache": True,
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
	dest_fstab.write("# Android fstab file." + "\n")
	dest_fstab.write("# The filesystem that contains the filesystem checker binary (typically /system) cannot" + "\n")
	dest_fstab.write("# specify MF_CHECK, and must come before any filesystems that do specify MF_CHECK" + "\n")
	dest_fstab.write("\n")
	dest_fstab.write("# mount point       fstype    device                                                                flags" + "\n")
	for entry in fstab_entries:
		if not entry.startswith("#") and entry != "":
			partition_path = entry.split()[0]
			partition_name = entry.split()[1]
			partition_fs = entry.split()[2]
			if allowed_partitions.get(partition_name, False):
				name_fs_space_int = default_name_fs_space - len(partition_name)
				fs_path_space_int = default_fs_path_space - len(partition_fs)
				path_flags_space_int = default_path_flags_space - len(partition_path)
				name_fs_space = " "
				fs_path_space = " "
				path_flags_space = " "
				for _ in itertools.repeat(None, name_fs_space_int):
					name_fs_space += " "
				for _ in itertools.repeat(None, fs_path_space_int):
					fs_path_space += " "
				for _ in itertools.repeat(None, path_flags_space_int):
					path_flags_space += " "
				dest_fstab.write(partition_name + name_fs_space + partition_fs + fs_path_space + partition_path + path_flags_space + partition_flags.get(partition_name, "") + "\n")
				if partition_needs_image_entry.get(partition_name, False):
					name_fs_space_int = default_name_fs_space - len(partition_name + "_image")
					name_fs_space = " "
					for _ in itertools.repeat(None, name_fs_space_int):
						name_fs_space += " "
					dest_fstab.write(partition_name + "_image" + name_fs_space + "emmc" + fs_path_space + partition_path + path_flags_space + partition_flags.get(partition_name + "_image", "") + "\n")
	orig_fstab.close()
	dest_fstab.close()

def open_file_and_read(target):
	file = open(target)
	result = file.read()
	file.close()
	result = result.split('\n', 1)[0]
	return result

def printhelp():
	print("Usage: start.py <recovery image path>")
