#
# Copyright (C) 2020 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from git import Repo
from pathlib import Path
from shutil import rmtree
from twrpdtgen.info_extractors.buildprop import BuildPropReader
from twrpdtgen.twrp_dt_gen import debug

class DeviceTree:
	"""
	A class representing a device tree

	It initialize a basic device tree structure
	and save the location of some important files
	"""
	def __init__(self, build_prop: BuildPropReader, output_path: Path, no_git=False) -> None:
		"""Initialize the device tree class."""
		self.build_prop = build_prop
		self.codename = self.build_prop.codename
		self.manufacturer = self.build_prop.manufacturer
		self.path = output_path / self.manufacturer / self.codename
		self.prebuilt_path = self.path / "prebuilt"
		self.recovery_root_path = self.path / "recovery" / "root"

		debug("Creating device tree folders...")
		if self.path.is_dir():
			rmtree(self.path, ignore_errors=True)
		self.path.mkdir(parents=True)
		self.prebuilt_path.mkdir(parents=True)
		self.recovery_root_path.mkdir(parents=True)

		self.fstab = self.path / "recovery.fstab"
		self.dt_image = self.prebuilt_path / "dt.img"
		self.dtb_image = self.prebuilt_path / "dtb.img"
		self.dtbo_image = self.prebuilt_path / "dtbo.img"

		if not no_git:
			self.git_repo = Repo.init(self.path)
