#
# Copyright (C) 2021 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from itertools import repeat
from pathlib import Path

FSTAB_HEADER = "# mount point       fstype    device                                                                flags\n"

# Partitions used during the boot process
BOOTLOADER_PARTITIONS = [
	"boot",
	"vendor_boot",
	"recovery",
	"dtbo",
	"misc",
]

# Partitions containing Android userspace libs and apps
SYSTEM_PARTITIONS = [
	"system",
	"system_ext",
	"vendor",
	"product",
	"odm",
]

# Partitions containing user data
ANDROID_USER_PARTITIONS = [
	"cache",
	"data",
]

# Partitions containing OEM or platform files, like firmwares
OEM_PARTITIONS = [
	"cust",
	"firmware",
	"persist",
]

# Partitions that can be backed up
PARTITION_BACKUP_FLAG = []
PARTITION_BACKUP_FLAG += BOOTLOADER_PARTITIONS
PARTITION_BACKUP_FLAG += SYSTEM_PARTITIONS

# Partitions that needs a fstab entry variant of type raw
PARTITION_NEEDS_IMAGE_ENTRY = []
PARTITION_NEEDS_IMAGE_ENTRY += SYSTEM_PARTITIONS
PARTITION_NEEDS_IMAGE_ENTRY += [
	"cust",
	"persist",
]

# Alternative partition mount points
PARTITION_ALTERNATE_MOUNT_POINT = {
	"/": "/system",
	"/system_root": "/system",
	"/sdcard": "/sdcard1",
}

class FstabEntry:
	"""
	A class representing a fstab entry
	"""
	def __init__(self, line: list) -> None:
		# Find out the syntax
		if line[1] in ["auto", "emmc", "ext4", "f2fs", "vfat", "squashfs"]:
			# TWRP syntax
			mount_point_location = 0
			fstype_location = 1
			device_location = 2
			flags_location = -1
		else:
			# AOSP syntax
			device_location = 0
			mount_point_location = 1
			fstype_location = 2
			flags_location = -1

		# Parse elements
		self.mount_point = line[mount_point_location]
		self.mount_point = PARTITION_ALTERNATE_MOUNT_POINT.get(self.mount_point, self.mount_point)
		if self.mount_point.count("/") > 1:
			self.mount_point = f"/{self.mount_point.rsplit('/', 1)[1]}"

		self.fstype = line[fstype_location]
		self.device = line[device_location]
		self.fsflags = line[flags_location]

		# Create a readable name
		if self.mount_point.startswith("/"):
			self.name = self.mount_point[1:]
		else:
			self.name = self.mount_point
		self.displayed_name = self.name.capitalize()
		is_image = self.name.endswith("_image") or self.name in BOOTLOADER_PARTITIONS
		if is_image and self.name not in BOOTLOADER_PARTITIONS:
			self.displayed_name = self.displayed_name.replace("_image", " image")

		# Put together TWRP flags
		self.flags = ['display="{}"'.format(self.displayed_name)]
		if is_image:
			self.flags += ['backup=1']
			self.flags += ['flashimg=1']
		else:
			if self.name in PARTITION_BACKUP_FLAG:
				self.flags += ['backup=1']
		if not self.device.startswith("/"):
			self.flags += ['logical']
		if 'slotselect' in self.fsflags:
			self.flags += ['slotselect']

class Fstab:
	def __init__(self, fstab: Path):
		self.fstab = fstab
		self.entries = []

		for line in self.fstab.read_text().splitlines():
			line = line.split()
			if len(line) < 2:
				continue
			if line[0].startswith("#"):
				continue

			self.entries.append(FstabEntry(line))

	def format(self):
		mount_point_len_max = 0
		fstype_len_max = 0
		device_len_max = 0

		for entry in self.entries:
			mount_point_len = len(entry.mount_point)
			if mount_point_len > mount_point_len_max:
				mount_point_len_max = mount_point_len

			fstype_len = len(entry.fstype)
			if fstype_len > fstype_len_max:
				fstype_len_max = fstype_len

			device_len = len(entry.device)
			if device_len > device_len_max:
				device_len_max = device_len

		mount_point_len_max += 5
		fstype_len_max += 5
		device_len_max += 5

		result = FSTAB_HEADER
		for entry in self.entries:
			mount_point_space = ""
			fstype_space = ""
			device_space = ""
			for _ in repeat(None, mount_point_len_max - len(entry.mount_point)):
				mount_point_space += " "
			for _ in repeat(None, fstype_len_max - len(entry.fstype)):
				fstype_space += " "
			for _ in repeat(None, device_len_max - len(entry.device)):
				device_space += " "
			result += f"{entry.mount_point}{mount_point_space}{entry.fstype}{fstype_space}{entry.device}{device_space}flags={';'.join(entry.flags)}\n"

		return result
