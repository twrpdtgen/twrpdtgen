#
# Copyright (C) 2021 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from git import Repo
from pathlib import Path
from shutil import copyfile, rmtree
from twrpdtgen import __version__ as version
from twrpdtgen.utils.aikmanager import AIKManager
from twrpdtgen.utils.buildprop import BuildProp
from twrpdtgen.utils.deviceinfo import DeviceInfo, ARCH_ARM, ARCH_ARM64
from twrpdtgen.utils.fstab import Fstab
from twrpdtgen.utils.logging import LOGD
from twrpdtgen.utils.template import render_template

BUILDPROP_LOCATIONS = [Path() / "default.prop",
                       Path() / "prop.default",]
BUILDPROP_LOCATIONS += [Path() / dir / "build.prop"
                        for dir in ["system", "vendor"]]
BUILDPROP_LOCATIONS += [Path() / dir / "etc" / "build.prop"
                        for dir in ["system", "vendor"]]

FSTAB_LOCATIONS = [Path() / "etc" / "recovery.fstab"]
FSTAB_LOCATIONS += [Path() / dir / "etc" / "recovery.fstab"
                    for dir in ["system", "vendor"]]

INIT_RC_LOCATIONS = [Path()]
INIT_RC_LOCATIONS += [Path() / dir / "etc" / "init"
                      for dir in ["system", "vendor"]]

class DeviceTree:
	"""
	A class representing a device tree

	It initialize a basic device tree structure
	and save the location of some important files
	"""
	def __init__(self, image: Path):
		"""Initialize the device tree class."""
		self.image = image

		# Check if the image exists
		if not self.image.is_file():
			raise FileNotFoundError("Specified file doesn't exist")

		# Extract the image
		self.aik = AIKManager(image)

		LOGD("Getting device infos...")
		self.buildprop = None
		for buildprop in [self.aik.ramdisk_path / location for location in BUILDPROP_LOCATIONS]:
			if buildprop.is_file():
				self.buildprop = BuildProp(buildprop)
				break

		if self.buildprop is None:
			raise AssertionError("Couldn't find any build.prop")

		LOGD(f"Using {self.buildprop} as build.prop")
		self.deviceinfo = DeviceInfo(self.buildprop)

		# Create a new kernel name from arch
		self.kernel_name = self.deviceinfo.kernel_name
		if (self.deviceinfo.arch in [ARCH_ARM, ARCH_ARM64]
				and (self.aik.dt_image is None and self.aik.dtb_image is None)):
			self.kernel_name += "-dtb"

		# Generate fstab
		self.fstab = None
		for fstab in [self.aik.ramdisk_path / location for location in FSTAB_LOCATIONS]:
			if not fstab.is_file():
				continue

			LOGD(f"Generating fstab using {fstab} as reference...")
			self.fstab = Fstab(fstab)
			break

		if self.fstab is None:
			raise AssertionError("fstab not found")

		# Search for init rc files
		self.init_rcs = []
		for init_rc_path in [self.aik.ramdisk_path / location for location in INIT_RC_LOCATIONS]:
			if not init_rc_path.is_dir():
				continue

			self.init_rcs += [init_rc for init_rc in init_rc_path.iterdir()
			                  if init_rc.name.endswith(".rc") and init_rc.name != "init.rc"]

	def dump_to_folder(self, output_path: Path, git: bool = False) -> Path:
		device_tree_folder = output_path / self.deviceinfo.manufacturer / self.deviceinfo.codename
		prebuilt_path = device_tree_folder / "prebuilt"
		recovery_root_path = device_tree_folder / "recovery" / "root"

		LOGD("Creating device tree folders...")
		if device_tree_folder.is_dir():
			rmtree(device_tree_folder, ignore_errors=True)
		device_tree_folder.mkdir(parents=True)
		prebuilt_path.mkdir(parents=True)
		recovery_root_path.mkdir(parents=True)

		# Fill makefiles
		LOGD("Creating Android.mk...")
		self._render_template(device_tree_folder, "Android.mk")

		LOGD("Creating AndroidProducts.mk...")
		self._render_template(device_tree_folder, "AndroidProducts.mk")

		LOGD("Creating BoardConfig.mk...")
		self._render_template(device_tree_folder, "BoardConfig.mk")

		LOGD("Creating device.mk...")
		self._render_template(device_tree_folder, "device.mk")

		LOGD(f"Creating omni_{self.deviceinfo.codename}.mk...")
		self._render_template(device_tree_folder, "omni.mk", out_file=f"omni_{self.deviceinfo.codename}.mk")

		LOGD("Creating vendorsetup.sh...")
		self._render_template(device_tree_folder, "vendorsetup.sh")

		LOGD("Copying kernel...")
		if self.aik.kernel is not None:
			copyfile(self.aik.kernel, prebuilt_path / self.kernel_name)
		if self.aik.dt_image is not None:
			copyfile(self.aik.dt_image, prebuilt_path / "dt.img")
		if self.aik.dtb_image is not None:
			copyfile(self.aik.dtb_image, prebuilt_path / "dtb.img")
		if self.aik.dtbo_image is not None:
			copyfile(self.aik.dtbo_image, prebuilt_path / "dtbo.img")

		LOGD("Copying fstab...")
		with open(device_tree_folder / "recovery.fstab", 'w') as f:
			f.write(self.fstab.format())

		LOGD("Copying init scripts...")
		for init_rc in self.init_rcs:
			copyfile(init_rc, recovery_root_path / init_rc.name, follow_symlinks=True)

		if not git:
			return device_tree_folder

		# Create a git repo
		LOGD("Creating git repo...")

		git_repo = Repo.init(device_tree_folder)
		git_config_reader = git_repo.config_reader()
		git_config_writer = git_repo.config_writer()

		try:
			git_global_email, git_global_name = git_config_reader.get_value('user', 'email'), git_config_reader.get_value('user', 'name')
		except Exception:
			git_global_email, git_global_name = None, None

		if git_global_email is None or git_global_name is None:
			git_config_writer.set_value('user', 'email', 'barezzisebastiano@gmail.com')
			git_config_writer.set_value('user', 'name', 'Sebastiano Barezzi')

		git_repo.index.add(["*"])
		commit_message = self._render_template(None, "commit_message", to_file=False)
		git_repo.index.commit(commit_message)

		return device_tree_folder

	def _render_template(self, *args, **kwargs):
		return render_template(*args,
		                       aik=self.aik,
		                       deviceinfo=self.deviceinfo,
		                       fstab=self.fstab,
		                       kernel_name=self.kernel_name,
		                       flash_block_size=(str(int(self.aik.pagesize) * 64)
		                                         if self.aik.pagesize is not None
		                                         else None),
		                       version=version,
		                       **kwargs)

	def cleanup(self):
		# Cleanup
		self.aik.cleanup()
