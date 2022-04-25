#
# Copyright (C) 2022 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from datetime import datetime
from git import Repo
from pathlib import Path
from sebaubuntu_libs.libaik import AIKManager
from sebaubuntu_libs.libfstab import Fstab
from sebaubuntu_libs.liblogging import LOGD
from sebaubuntu_libs.libprop import BuildProp
from shutil import copyfile, rmtree
from twrpdtgen import __version__ as version
from twrpdtgen.utils.device_info import DeviceInfo, ARCH_ARM, ARCH_ARM64
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

		self.current_year = str(datetime.now().year)

		# Check if the image exists
		if not self.image.is_file():
			raise FileNotFoundError("Specified file doesn't exist")

		# Extract the image
		self.aik_manager = AIKManager()
		self.image_info = self.aik_manager.unpackimg(image)

		LOGD("Getting device infos...")
		self.build_prop = BuildProp()
		for build_prop in [self.image_info.ramdisk / location for location in BUILDPROP_LOCATIONS]:
			if not build_prop.is_file():
				continue

			self.build_prop.import_props(build_prop)

		self.device_info = DeviceInfo(self.build_prop)

		# Create a new kernel name from arch
		self.kernel_name = self.device_info.kernel_name
		if (self.device_info.arch in [ARCH_ARM, ARCH_ARM64]
				and (self.image_info.dt is None and self.image_info.dtb is None)):
			self.kernel_name += "-dtb"

		# Generate fstab
		self.fstab = None
		for fstab in [self.image_info.ramdisk / location for location in FSTAB_LOCATIONS]:
			if not fstab.is_file():
				continue

			LOGD(f"Generating fstab using {fstab} as reference...")
			self.fstab = Fstab(fstab)
			break

		if self.fstab is None:
			raise AssertionError("fstab not found")

		# Search for init rc files
		self.init_rcs: list[Path] = []
		for init_rc_path in [self.image_info.ramdisk / location for location in INIT_RC_LOCATIONS]:
			if not init_rc_path.is_dir():
				continue

			self.init_rcs += [init_rc for init_rc in init_rc_path.iterdir()
			                  if init_rc.name.endswith(".rc") and init_rc.name != "init.rc"]

	def dump_to_folder(self, output_path: Path, git: bool = False) -> Path:
		device_tree_folder = output_path / self.device_info.manufacturer / self.device_info.codename
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

		LOGD(f"Creating omni_{self.device_info.codename}.mk...")
		self._render_template(device_tree_folder, "omni.mk", out_file=f"omni_{self.device_info.codename}.mk")

		LOGD("Creating vendorsetup.sh...")
		self._render_template(device_tree_folder, "vendorsetup.sh")

		LOGD("Copying kernel...")
		if self.image_info.kernel is not None:
			copyfile(self.image_info.kernel, prebuilt_path / self.kernel_name)
		if self.image_info.dt is not None:
			copyfile(self.image_info.dt, prebuilt_path / "dt.img")
		if self.image_info.dtb is not None:
			copyfile(self.image_info.dtb, prebuilt_path / "dtb.img")
		if self.image_info.dtbo is not None:
			copyfile(self.image_info.dtbo, prebuilt_path / "dtbo.img")

		LOGD("Copying fstab...")
		(device_tree_folder / "recovery.fstab").write_text(self.fstab.format(twrp=True))

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
		                       current_year=self.current_year,
		                       device_info=self.device_info,
		                       fstab=self.fstab,
		                       image_info=self.image_info,
		                       kernel_name=self.kernel_name,
		                       flash_block_size=(str(int(self.image_info.pagesize) * 64)
		                                         if self.image_info.pagesize is not None
		                                         else None),
		                       version=version,
		                       **kwargs)

	def cleanup(self):
		# Cleanup
		self.aik_manager.cleanup()
