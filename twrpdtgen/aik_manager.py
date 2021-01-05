from pathlib import Path
from platform import system
from shutil import copyfile, rmtree
from subprocess import Popen, PIPE, call
from tempfile import TemporaryDirectory
from typing import Union

from git import Repo

from twrpdtgen import current_path
from twrpdtgen.twrp_dt_gen import info
from twrpdtgen.misc import handle_remove_readonly


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
		# TODO Check if AIK extract is successful
		if system() == "Linux":
			aik_process = Popen([self.path / "unpackimg.sh", "--nosudo", new_recovery_image],
								stdout=PIPE, stderr=PIPE, universal_newlines=True)
			_, _ = aik_process.communicate()
		elif system() == "Windows":
			call([self.path / "unpackimg.bat", new_recovery_image])
		else:
			raise NotImplementedError(f"{system()} is not supported!")

	def cleanup(self):
		if not self.is_debug:
			self.tempdir.cleanup()
