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
from twrpdtgen.utils.deviceinfo import DeviceInfo, ARCH_TO_STRING, ARCH_ARM, ARCH_ARM64
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
	def __init__(self, image: Path, debug = False):
		"""Initialize the device tree class."""
		self.image = image

		# Check if the image exists
		if not self.image.is_file():
			raise FileNotFoundError("Specified file doesn't exist")

		# Extract the image
		self.aik = AIKManager(image, debug=debug)

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
		render_template(device_tree_folder, "Android.mk.jinja2",
		                device_codename=self.deviceinfo.codename)

		LOGD("Creating AndroidProducts.mk...")
		render_template(device_tree_folder, "AndroidProducts.mk.jinja2",
						device_codename=self.deviceinfo.codename)

		LOGD("Creating BoardConfig.mk...")
		render_template(device_tree_folder, "BoardConfig.mk.jinja2",
						device_manufacturer=self.deviceinfo.manufacturer,
						device_codename=self.deviceinfo.codename,
						device_is_ab=self.deviceinfo.device_is_ab,
						device_platform=self.deviceinfo.platform,
						device_arch=ARCH_TO_STRING[self.deviceinfo.arch],
						device_pixel_format = self.deviceinfo.device_pixel_format,
						board_name=self.aik.board_name,
						recovery_size=self.aik.recovery_size,
						cmdline=self.aik.cmdline,
						kernel=self.aik.kernel,
						kernel_name=self.kernel_name,
						dt_image=self.aik.dt_image,
						dtb_image=self.aik.dtb_image,
						dtbo_image=self.aik.dtbo_image,
						header_version=self.aik.header_version,
						base_address=self.aik.base_address,
						pagesize=self.aik.pagesize,
						ramdisk_offset=self.aik.ramdisk_offset,
						tags_offset=self.aik.tags_offset,
						ramdisk_compression=self.aik.ramdisk_compression,
						flash_block_size=(str(int(self.aik.pagesize) * 64)
						                  if self.aik.pagesize is not None else None))

		LOGD("Creating device.mk...")
		render_template(device_tree_folder, "device.mk.jinja2",
						device_codename=self.deviceinfo.codename,
						device_manufacturer=self.deviceinfo.manufacturer,
						device_platform=self.deviceinfo.platform,
						device_is_ab=self.deviceinfo.device_is_ab)

		LOGD(f"Creating omni_{self.deviceinfo.codename}.mk...")
		render_template(device_tree_folder, "omni.mk.jinja2", out_file=f"omni_{self.deviceinfo.codename}.mk",
						device_codename=self.deviceinfo.codename,
						device_manufacturer=self.deviceinfo.manufacturer,
						device_brand=self.deviceinfo.brand,
						device_model=self.deviceinfo.model,
						device_has_64bit_arch=self.deviceinfo.device_has_64bit_arch)

		LOGD("Creating vendorsetup.sh...")
		render_template(device_tree_folder, "vendorsetup.sh.jinja2",
		                device_codename=self.deviceinfo.codename)

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
		commit_message = render_template(None, "commit_message.jinja2", to_file=False,
		                                 device_codename=self.deviceinfo.codename,
		                                 device_arch=self.deviceinfo.arch,
		                                 device_manufacturer=self.deviceinfo.manufacturer,
		                                 device_brand=self.deviceinfo.brand,
		                                 device_model=self.deviceinfo.model,
		                                 version=version)
		git_repo.index.commit(commit_message)

		return device_tree_folder

	def cleanup(self):
		# Cleanup
		self.aik.cleanup()
