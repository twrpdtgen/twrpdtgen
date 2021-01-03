#
# Copyright (C) 2020 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from itertools import repeat
from pathlib import Path

default_name_fs_space = 20
default_fs_device_space = 10
default_device_flags_space = 70

# TWRP syntax
partition_name_location = 0
partition_fstype_location = 1
partition_device_location = 2

# Partitions used during the boot process
bootloader_partitions = [
	"/boot",
	"/vendor_boot",
	"/recovery",
	"/dtbo",
	"/misc"
]

# Partitions containing Android userspace libs and apps
system_partitions = [
	"/system",
	"/system_ext",
	"/vendor",
	"/product",
	"/odm"
]

# Partitions containing user data
android_user_partitions = [
	"/cache",
	"/data",
]

# Partitions containing OEM or platform files, like firmwares
oem_partitions = [
	"/cust",
	"/firmware",
	"/persist",
]

allowed_partitions = []
allowed_partitions += bootloader_partitions
allowed_partitions += system_partitions
allowed_partitions += android_user_partitions
allowed_partitions += oem_partitions

# Partitions that can be backed up
partition_backup_flag = []
partition_backup_flag += bootloader_partitions
partition_backup_flag += system_partitions

# Partitions that needs a fstab entry variant of type raw
partition_needs_image_entry = []
partition_needs_image_entry += system_partitions
partition_needs_image_entry += [
	"/cust",
	"/persist"
]

# Alternative partition mount points
partition_alternative_name = {
	"/": "/system",
	"/system_root": "/system"
}

class FstabEntry:
	"""
	A class representing a fstab entry
	"""
	def __init__(self, line: list) -> None:
		# Find out the syntax
		if line[1] in ["auto", "emmc", "ext4", "f2fs", "vfat", "squashfs"]:
			# TWRP syntax
			name_location = 0
			fstype_location = 1
			device_location = 2
		else:
			# AOSP syntax
			device_location = 0
			name_location = 1
			fstype_location = 2

		# Parse elements
		self.name = line[name_location]
		self.name = partition_alternative_name.get(self.name, self.name)
		self.fstype = line[fstype_location]
		self.device = line[device_location]

		# Create a readable name
		self.human_name = self.name
		if self.name.startswith("/"):
			self.human_name = self.human_name[1:]
		self.human_name = self.human_name.capitalize()
		is_image = True if (self.name.endswith("_image") or self.name in bootloader_partitions) else False
		if is_image and self.name not in bootloader_partitions:
			self.human_name = self.human_name[:-len("_image")]
			self.human_name += " image"

		# Put together TWRP flags
		self.flags = ['display="{}"'.format(self.human_name)]
		if is_image:
			self.flags += ['backup=1']
			self.flags += ['flashimg=1']
		else:
			if self.name in partition_backup_flag:
				self.flags += ['backup=1']
		if not self.device.startswith("/"):
			self.flags += ['logical']

	def get_formatted_line(self) -> str:
		"""
		Return a TWRP fstab line properly formatted
		"""
		name_fs_space = " "
		fs_device_space = " "
		device_flags_space = " "
		name_fs_space_int = default_name_fs_space - 1 - len(self.name)
		fs_device_space_int = default_fs_device_space - 1 - len(self.fstype)
		device_flags_space_int = default_device_flags_space - 1 - len(self.device)
		for _ in repeat(None, name_fs_space_int):
			name_fs_space += " "
		for _ in repeat(None, fs_device_space_int):
			fs_device_space += " "
		for _ in repeat(None, device_flags_space_int):
			device_flags_space += " "
		readable_flags = "flags="
		for flag in self.flags:
			readable_flags += flag + ";"
		return self.name + name_fs_space + self.fstype + fs_device_space + self.device + device_flags_space + readable_flags

	def raw_image(self) -> __init__:
		"""
		Return a FstabEntry containing the raw equivalent of itself
		"""
		return FstabEntry([self.name + "_image", "emmc", self.device])

def make_twrp_fstab(old_fstab: Path, new_fstab: Path):
	orig_fstab = open(old_fstab)
	dest_fstab = open(new_fstab, "w")
	fstab_entries = orig_fstab.read()
	fstab_entries = fstab_entries.splitlines()
	dest_fstab.write("# mount point       fstype    device                                                                flags" + "\n")
	for entry in fstab_entries:
		entry_split = entry.split()
		if not entry.startswith("#") and len(entry_split) >= 2:
			fstab_entry = FstabEntry(entry_split)
			if fstab_entry.name not in allowed_partitions:
				continue
			dest_fstab.write(fstab_entry.get_formatted_line() + "\n")
			if fstab_entry.name in partition_needs_image_entry:
				dest_fstab.write(fstab_entry.raw_image().get_formatted_line() + "\n")

	orig_fstab.close()
	dest_fstab.close()
