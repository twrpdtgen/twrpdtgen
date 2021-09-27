#
# Copyright (C) 2021 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from git import Repo
from pathlib import Path
from platform import system
from shutil import copyfile, rmtree, which
from stat import S_IWRITE
from subprocess import check_output, STDOUT, CalledProcessError
from tempfile import TemporaryDirectory
from twrpdtgen import current_path
from twrpdtgen.utils.logging import LOGD

ALLOWED_OS = [
	"Linux",
	"Darwin",
]

def handle_remove_readonly(func, path, _):
	Path(path).chmod(S_IWRITE)
	func(path)

class AIKManager:
	"""
	This class is responsible for dealing with AIK tasks
	such as cloning, updating, and extracting recovery images.
	"""

	def __init__(self, image: Path, debug=False):
		"""Initialize AIKManager class."""
		self.debug = debug

		if system() not in ALLOWED_OS:
			raise NotImplementedError(f"{system()} is not supported!")

		# Check whether cpio package is installed
		if which("cpio") is None:
			raise RuntimeError("cpio package is not installed")

		if not self.debug:
			self.tempdir = TemporaryDirectory()
			self.path = Path(self.tempdir.name)
		else:
			self.path = current_path / "extract"
		if self.path.is_dir():
			rmtree(self.path, ignore_errors=False, onerror=handle_remove_readonly)

		self.images_path = self.path / "split_img"
		self.ramdisk_path = self.path / "ramdisk"

		LOGD("Cloning AIK...")
		Repo.clone_from("https://github.com/SebaUbuntu/AIK-Linux-mirror", self.path)

		new_image = self.path / "recovery.img"
		copyfile(image, new_image)

		command = [self.path / "unpackimg.sh", "--nosudo", new_image]

		try:
			process = check_output(command, stderr=STDOUT, universal_newlines=True)
		except CalledProcessError as e:
			returncode = e.returncode
			output = e.output
		else:
			returncode = 0
			output = process

		if returncode != 0:
			if self.debug:
				print(output)
			raise RuntimeError(f"AIK extraction failed, return code {returncode}")

		kernel = self.get_extracted_info("kernel")
		self.kernel = kernel if kernel.is_file() else None
		dt_image = self.get_extracted_info("dt")
		self.dt_image = dt_image if dt_image.is_file() else None
		dtb_image = self.get_extracted_info("dtb")
		self.dtb_image = dtb_image if dtb_image.is_file() else None
		self.dtbo_image = None
		for name in ["dtbo", "recovery_dtbo"]:
			dtbo_image = self.get_extracted_info(name)
			if dtbo_image.is_file():
				self.dtbo_image = dtbo_image

		self.base_address = self.read_recovery_file("base")
		self.board_name = self.read_recovery_file("board")
		self.cmdline = self.read_recovery_file("cmdline")
		self.header_version = self.read_recovery_file("header_version", default="0")
		self.recovery_size = self.read_recovery_file("origsize")
		self.pagesize = self.read_recovery_file("pagesize")
		self.ramdisk_compression = self.read_recovery_file("ramdiskcomp")
		self.ramdisk_offset = self.read_recovery_file("ramdisk_offset")
		self.tags_offset = self.read_recovery_file("tags_offset")

	def read_recovery_file(self, fragment: str, default: str = None) -> str:
		file = self.get_extracted_info(fragment)
		return file.read_text().splitlines()[0].strip() if file.exists() else default

	def get_extracted_info(self, fragment: str) -> Path:
		return self.images_path / ("recovery.img-" + fragment)

	def cleanup(self):
		if not self.debug:
			self.tempdir.cleanup()
