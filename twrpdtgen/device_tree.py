#
# Copyright (C) 2020 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from git import Repo
from logging import debug
from pathlib import Path
from shutil import copyfile, rmtree
from twrpdtgen import __version__ as version
from twrpdtgen.info_extractors.buildprop import BuildPropReader
from twrpdtgen.utils.aik_manager import AIKManager
from twrpdtgen.utils.build_prop import BuildProp
from twrpdtgen.utils.constants import FSTAB_LOCATIONS, INIT_RC_LOCATIONS
from twrpdtgen.utils.fstab import make_twrp_fstab
from twrpdtgen.utils.huawei import HuaweiUtils
from twrpdtgen.utils.kernel import get_kernel_name
from twrpdtgen.utils.template import render_template

class DeviceTree:
	"""
	A class representing a device tree

	It initialize a basic device tree structure
	and save the location of some important files
	"""
	def __init__(self, output_path: Path, recovery_image=None,
				 no_git=False, keep_aik=False, huawei=False,
				 recovery_kernel=None, recovery_ramdisk=None, recovery_vendor=None) -> None:
		"""Initialize the device tree class."""

		if not huawei:
			self.images = [recovery_image]
		else:
			self.images = [recovery_kernel, recovery_ramdisk, recovery_vendor]

		for image in self.images:
			# Check if the provided images are None
			if image is None:
				raise FileNotFoundError("Missing image argument")
			# Check if the image exists
			elif not image.is_file():
				raise FileNotFoundError("Specified file doesn't exist")

		if not huawei:
			# Extract the image
			aik = AIKManager(keep_aik)
			aik.extract(recovery_image)
		else:
			huawei_utils = HuaweiUtils(recovery_kernel, recovery_ramdisk, recovery_vendor, is_debug=keep_aik)
			aik = huawei_utils.extract()

		# Parse build prop
		debug("Getting device infos...")
		if aik.buildprop is None:
			raise AssertionError("Couldn't find any build.prop")
		debug("Using " + str(aik.buildprop) + " as build.prop")
		self.build_prop = BuildProp(aik.buildprop)
		self.build_prop_reader = BuildPropReader(self.build_prop)

		self.codename = self.build_prop_reader.codename
		self.manufacturer = self.build_prop_reader.manufacturer
		self.path = output_path / self.manufacturer / self.codename
		self.prebuilt_path = self.path / "prebuilt"
		self.recovery_root_path = self.path / "recovery" / "root"

		# Initialize path variables
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

		debug("Copying kernel...")
		# Create a new kernel name from arch
		new_kernel_name = get_kernel_name(self.build_prop_reader.arch)
		if self.build_prop_reader.arch in ("arm", "arm64") and (aik.dt_image is None and aik.dtb_image is None):
			new_kernel_name += "-dtb"

		# Copy kernel/dt/dtb/dtbo
		if aik.kernel is not None:
			copyfile(aik.kernel, self.prebuilt_path / new_kernel_name)
		if aik.dt_image is not None:
			copyfile(aik.dt_image, self.dt_image)
		if aik.dtb_image is not None:
			copyfile(aik.dtb_image, self.dtb_image)
		if aik.dtbo_image is not None:
			copyfile(aik.dtbo_image, self.dtbo_image)

		# Decide whether a fstab should be generated
		if Path(aik.ramdisk_path / "etc" / "twrp.fstab").is_file():
			debug("Found a TWRP fstab, copying it...")
			copyfile(aik.ramdisk_path / "etc" / "twrp.fstab", self.fstab)
		else:
			for fstab in FSTAB_LOCATIONS:
				fstab = aik.ramdisk_path / fstab
				debug(f"Checking {fstab}")
				if not (aik.ramdisk_path / fstab).is_file():
					continue
				debug(f"Generating fstab, using {fstab} as reference...")
				make_twrp_fstab(fstab, self.fstab)
				break
		if not self.fstab.is_file():
			raise AssertionError("fstab not found")

		# Search for init rc files
		for init_rc_path in INIT_RC_LOCATIONS:
			init_rc_path = aik.ramdisk_path / init_rc_path
			if not init_rc_path.is_dir():
				continue
			debug(f"Checking {init_rc_path} for init rc files")
			for file in init_rc_path.iterdir():
				file = file
				if not file.name.endswith(".rc") or file.name == "init.rc":
					continue
				debug(f"Found an init rc file, {file.name}")
				copyfile(file, self.recovery_root_path / file.name, follow_symlinks=True)

		# Fill makefiles
		debug("Creating Android.mk...")
		render_template(self.path, "Android.mk.jinja2", device_codename=self.build_prop_reader.codename)

		debug("Creating AndroidProducts.mk...")
		render_template(self.path, "AndroidProducts.mk.jinja2",
						device_codename=self.build_prop_reader.codename)

		debug("Creating BoardConfig.mk...")
		render_template(self.path, "BoardConfig.mk.jinja2",
						device_manufacturer=self.build_prop_reader.manufacturer,
						device_codename=self.build_prop_reader.codename,
						device_is_ab=self.build_prop_reader.device_is_ab,
						device_platform=self.build_prop_reader.platform,
						device_arch=self.build_prop_reader.arch,
						board_name=aik.board_name,
						recovery_size=aik.recovery_size,
						cmdline=aik.cmdline,
						kernel=aik.kernel,
						kernel_name=new_kernel_name,
						dt_image=aik.dt_image,
						dtb_image=aik.dtb_image,
						dtbo_image=aik.dtbo_image,
						header_version=aik.header_version,
						base_address=aik.base_address,
						pagesize=aik.pagesize,
						ramdisk_offset=aik.ramdisk_offset,
						tags_offset=aik.tags_offset,
						ramdisk_compression=aik.ramdisk_compression,
						flash_block_size=str(int(aik.pagesize) * 64))

		debug("Creating device.mk...")
		render_template(self.path, "device.mk.jinja2",
						device_codename=self.build_prop_reader.codename,
						device_manufacturer=self.build_prop_reader.manufacturer,
						device_platform=self.build_prop_reader.platform,
						device_is_ab=self.build_prop_reader.device_is_ab)

		debug(f"Creating omni_{self.build_prop_reader.codename}.mk...")
		render_template(self.path, "omni.mk.jinja2", out_file=f"omni_{self.build_prop_reader.codename}.mk",
						device_codename=self.build_prop_reader.codename,
						device_manufacturer=self.build_prop_reader.manufacturer,
						device_brand=self.build_prop_reader.brand,
						device_model=self.build_prop_reader.model,
						device_has_64bit_arch=self.build_prop_reader.device_has_64bit_arch)

		debug("Creating vendorsetup.sh...")
		render_template(self.path, "vendorsetup.sh.jinja2", device_codename=self.build_prop_reader.codename)

		# Create a git repo
		if not no_git:
			git_config_reader = self.git_repo.config_reader()
			git_config_writer = self.git_repo.config_writer()
			try:
				git_global_email, git_global_name = git_config_reader.get_value('user', 'email'), git_config_reader.get_value('user', 'name')
			except:
				git_global_email, git_global_name = None, None
			if git_global_email is None or git_global_name is None:
				git_config_writer.set_value('user', 'email', 'barezzisebastiano@gmail.com')
				git_config_writer.set_value('user', 'name', 'Sebastiano Barezzi')
			self.git_repo.index.add(["*"])
			commit_message = render_template(None, "commit_message.jinja2", to_file=False,
											 device_codename=self.build_prop_reader.codename,
											 device_arch=self.build_prop_reader.arch,
											 device_manufacturer=self.build_prop_reader.manufacturer,
											 device_brand=self.build_prop_reader.brand,
											 device_model=self.build_prop_reader.model,
											 version=version)
			self.git_repo.index.commit(commit_message)

		# Cleanup
		aik.cleanup()
