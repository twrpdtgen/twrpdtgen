from logging import warning
from twrpdtgen.utils.build_prop import BuildProp

PARTITIONS = ["odm", "product", "system", "system_ext", "vendor"]

DEVICE_CODENAME = ["ro.product.device"] + [f"ro.product.{partition}.device" for partition in PARTITIONS]
DEVICE_MANUFACTURER = ["ro.product.manufacturer"] + [f"ro.product.{partition}.manufacturer" for partition in PARTITIONS]
DEVICE_BRAND = ["ro.product.brand"] + [f"ro.product.{partition}.brand" for partition in PARTITIONS]
DEVICE_MODEL = ["ro.product.model"] + [f"ro.product.{partition}.brand" for partition in PARTITIONS]
DEVICE_ARCH = ["ro.product.cpu.abi", "ro.product.cpu.abilist"]
DEVICE_IS_AB = ["ro.build.ab_update"]
DEVICE_PLATFORM = ["ro.board.platform", "ro.hardware.keystore", "ro.hardware.chipname"]
DEVICE_PIXEL_FORMAT = ["ro.minui.pixel_format"]

class BuildPropReader:
	"""
	This class is responsible for reading parse common build props needed for twrpdtgen
	by using BuildProp class.
	"""

	def __init__(self, build_prop: BuildProp):
		"""
		Parse common build props needed for twrpdtgen.
		"""
		self.build_prop = build_prop
		# Parse props
		self.codename = self.get_prop(DEVICE_CODENAME, "codename")
		self.manufacturer = self.get_prop(DEVICE_MANUFACTURER, "manufacturer").split()[0].lower()
		self.brand = self.get_prop(DEVICE_BRAND, "brand")
		self.model = self.get_prop(DEVICE_MODEL, "model")
		self.arch = self.parse_arch(self.get_prop(DEVICE_ARCH, "arch"))
		self.device_has_64bit_arch = self.arch in ("arm64", "x86_64")

		try:
			self.platform = self.get_prop(DEVICE_PLATFORM, "platform")
		except AssertionError:
			warning('Platform prop not found! Defaulting to "default"')
			self.platform = "default"

		try:
			self.device_is_ab = bool(self.get_prop(DEVICE_IS_AB, "A/B"))
		except AssertionError:
			self.device_is_ab = False

		try:
			self.device_pixel_format = self.get_prop(DEVICE_PIXEL_FORMAT, "pixel format")
		except AssertionError:
			self.device_pixel_format = None

	def get_prop(self, props: list, error: str):
		"""
		Parse multiple props names stored in arrays and return the first valid value.

		Raises AssertionError if no value is found
		"""
		for prop in props:
			prop_value = self.build_prop.get_prop(prop)
			if prop_value is not None:
				return prop_value
		raise AssertionError(f"Device {error} could not be found in build.prop")

	@staticmethod
	def parse_arch(arch: str) -> str:
		"""
		Parse architecture information from build.prop and return twrp arch
		:param arch: ro.product.cpu.abi or ro.product.cpu.abilist value
		:return: architecture information for twrp device tree
		"""
		if arch.startswith("arm64"):
			return "arm64"
		if arch.startswith("armeabi"):
			return "arm"
		if arch.startswith("x86"):
			return "x86"
		if arch.startswith("x86_64"):
			return "x86_64"
		if arch.startswith("mips"):
			return "mips"
		return "unknown"
