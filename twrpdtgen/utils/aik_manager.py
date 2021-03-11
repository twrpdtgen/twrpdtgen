from git import Repo
from logging import info
from pathlib import Path
from platform import system
from shutil import copyfile, rmtree
from stat import S_IWRITE
from subprocess import check_output, STDOUT, CalledProcessError
from tempfile import TemporaryDirectory
from twrpdtgen import current_path
from typing import Union

def handle_remove_readonly(func, path, _):
	Path(path).chmod(S_IWRITE)
	func(path)

class AIKManager:
	"""
	This class is responsible for dealing with AIK tasks
	such as cloning, updating, and extracting recovery images.
	"""

	def __init__(self, is_debug):
		"""
		AIKManager constructor method
		First, check if AIK path exists, if so, update AIK, else clone AIK.

		:param aik_path: Path object of AIK directory
		"""
		self.is_debug = is_debug
		if not self.is_debug:
			self.tempdir = TemporaryDirectory()
			self.path = Path(self.tempdir.name)
		else:
			self.path = current_path / "extract"
		if self.path.is_dir():
			rmtree(self.path, ignore_errors=False, onerror=handle_remove_readonly)

		self.images_path = self.path / "split_img"
		self.ramdisk_path = self.path / "ramdisk"

		info("Cloning AIK...")
		if system() == "Linux":
			Repo.clone_from("https://github.com/SebaUbuntu/AIK-Linux-mirror", self.path)
		elif system() == "Windows":
			Repo.clone_from("https://github.com/SebaUbuntu/AIK-Windows-mirror", self.path)

	def extract(self, recovery_image: Union[Path, str]) -> None:
		"""
		Extract an image using AIK.
		:param recovery_image: recovery image string or path object
		"""
		new_recovery_image = self.path / "recovery.img"
		copyfile(recovery_image, new_recovery_image)

		if system() == "Linux":
			command = [self.path / "unpackimg.sh", "--nosudo", new_recovery_image]
		elif system() == "Windows":
			command = [self.path / "unpackimg.bat", new_recovery_image]
		else:
			raise NotImplementedError(f"{system()} is not supported!")

		try:
			process = check_output(command, stderr=STDOUT, universal_newlines=True)
		except CalledProcessError as e:
			returncode = e.returncode
			output = e.output
		else:
			returncode = 0
			output = process

		if returncode != 0:
			if self.is_debug:
				print(output)
			raise RuntimeError(f"AIK extraction failed, return code {returncode}")

		self.get_image_infos()

	def get_image_infos(self):
		self.aik_images_path_base = str(self.images_path / "recovery.img-")
		kernel = self.get_extracted_info("zImage")
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
		self.base_address = self.read_recovery_file(self.get_extracted_info("base"))
		self.board_name = self.read_recovery_file(self.get_extracted_info("board"))
		self.cmdline = self.read_recovery_file(self.get_extracted_info("cmdline"))
		header_version = self.get_extracted_info("header_version")
		self.header_version = self.read_recovery_file(header_version) if header_version.exists() else "0"
		self.recovery_size = self.read_recovery_file(self.get_extracted_info("origsize"))
		self.pagesize = self.read_recovery_file(self.get_extracted_info("pagesize"))
		self.ramdisk_compression = self.read_recovery_file(self.get_extracted_info("ramdiskcomp"))
		self.ramdisk_offset = self.read_recovery_file(self.get_extracted_info("ramdisk_offset"))
		self.tags_offset = self.read_recovery_file(self.get_extracted_info("tags_offset"))

		# Get a usable build.prop to parse
		self.buildprop = None
		buildprop_locations = [self.ramdisk_path / "default.prop",
							   self.ramdisk_path / "vendor" / "build.prop",
							   self.ramdisk_path / "system" / "build.prop",
							   self.ramdisk_path / "system" / "etc" / "build.prop"]
		for folder in buildprop_locations:
			if folder.is_file():
				self.buildprop = folder
				break

	@staticmethod
	def read_recovery_file(file: Path) -> str:
		"""
		Read file contents
		:param file: file as a Path object
		:return: string of the first line of the file contents
		"""
		return file.read_text().splitlines()[0]

	def get_extracted_info(self, file: str) -> Path:
		return self.images_path / ("recovery.img-" + file)

	def cleanup(self):
		if not self.is_debug:
			self.tempdir.cleanup()
