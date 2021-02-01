#
# Copyright (C) 2020 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from shutil import copytree, rmtree, move
from twrpdtgen.utils.aik_manager import AIKManager, handle_remove_readonly

class HuaweiUtils:
	"""
	Huawei/Honor Utils
	"""
	def __init__(self, recovery_kernel, recovery_ramdisk, recovery_vendor, is_debug=False):
		"""
		Merge recovery_kernel, recovery_ramdisk and recovery_vendor
		into a single AIKManager class.

		Huawei/Honor on Kirin devices uses 3 different partitions for recovery.
		They split kernel, ramdisk and vendor folder.

		recovery_kernel: recovery image with a valid kernel and an empty ramdisk.

		recovery_ramdisk: recovery image with an empty kernel and a ramdisk.

		recovery_vendor: recovery image with an empty kernel and a ramdisk,
		which only contains /vendor. It is overlayed to recovery_ramdisk's ramdisk
		"""
		self.recovery_kernel = recovery_kernel
		self.recovery_ramdisk = recovery_ramdisk
		self.recovery_vendor = recovery_vendor
		self.is_debug = is_debug
	
	def extract(self):
		self.recovery_kernel_aik = AIKManager(self.is_debug)
		self.recovery_ramdisk_aik = AIKManager(False)
		self.recovery_vendor_aik = AIKManager(False)

		self.recovery_kernel_aik.extract(self.recovery_kernel)		
		self.recovery_ramdisk_aik.extract(self.recovery_ramdisk)
		self.recovery_vendor_aik.extract(self.recovery_vendor)

		self.ramdisk = self.recovery_kernel_aik.ramdisk_path

		if self.ramdisk.is_dir():
			rmtree(self.ramdisk, ignore_errors=False, onerror=handle_remove_readonly)
		move(self.recovery_ramdisk_aik.ramdisk_path, self.ramdisk)

		# Copy recovery_vendor ramdisk to recovery_ramdisk's vendor folder
		self.old_vendor_path = self.recovery_vendor_aik.ramdisk_path / "vendor"
		self.new_vendor_path = self.ramdisk / "vendor"
		if self.new_vendor_path.is_dir():
			rmtree(self.new_vendor_path, ignore_errors=False, onerror=handle_remove_readonly)
		elif self.new_vendor_path.is_file() or self.new_vendor_path.is_symlink():
			self.new_vendor_path.unlink()
		copytree(self.old_vendor_path, self.new_vendor_path)

		# Cleanup unneeded AIK folder
		self.recovery_ramdisk_aik.cleanup()
		self.recovery_vendor_aik.cleanup()

		# After the ramdisk fixes, reobtain image infos
		self.recovery_kernel_aik.get_image_infos()

		return self.recovery_kernel_aik
