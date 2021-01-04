"""
Device info reader class implementation.
"""

from pathlib import Path

kernel_names = {
	"arm": "zImage",
	"arm64": "Image.gz",
	"x86": "bzImage",
	"x86_64": "bzImage"
}

class RecoveryImageInfoReader:
	"""
	This class is responsible for reading device information from ramdisk
	"""
	# pylint: disable=too-many-instance-attributes, too-few-public-methods

	def __init__(self, aik_ramdisk_path: Path, aik_images_path: Path):
		"""
		Device info reader class constructor
		:param aik_ramdisk_path: Extracted ramdisk path as a Path object
		:param aik_images_path: Extracted images path as Path object
		"""
		self.aik_ramdisk_path = aik_ramdisk_path
		self.aik_images_path = aik_images_path
		self.aik_images_path_base = str(aik_images_path / "recovery.img-")
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
		self.kernel_name = ''

		# Get a usable build.prop to parse
		self.buildprop = None
		buildprop_locations = [self.aik_ramdisk_path / "default.prop",
							   self.aik_ramdisk_path / "vendor" / "build.prop",
							   self.aik_ramdisk_path / "system" / "build.prop",
							   self.aik_ramdisk_path / "system" / "etc" / "build.prop"]
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
		return self.aik_images_path / ("recovery.img-" + file)

	def get_kernel_name(self, arch: str) -> str:
		"""
		Get kernel name of the device
		:param arch: device architecture information from build.prop
		:return: string of the kernel name
		"""
		if self.kernel is not None:
			try:
				kernel_name = kernel_names[arch]
			except KeyError:
				kernel_name = "zImage"
			if arch in ("arm", "arm64") and (
					self.dt_image is None and self.dtb_image is None):
				kernel_name += "-dtb"
			self.kernel_name = kernel_name
			return kernel_name
		return ""
