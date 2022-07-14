#
# Copyright (C) 2022 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from distutils.util import strtobool
from sebaubuntu_libs.libandroid.props import BuildProp

PARTITIONS = [
	"",
	"bootimage.",
	"odm.",
	"product.",
	"system.",
	"system_ext.",
	"vendor.",
]

def get_product_props(value: str):
	return [f"ro.product.{partition}{value}" for partition in PARTITIONS]

DEVICE_CODENAME = get_product_props("device")
DEVICE_MANUFACTURER = get_product_props("manufacturer")
DEVICE_BRAND = get_product_props("brand")
DEVICE_MODEL = get_product_props("model")
DEVICE_ARCH = ["ro.product.cpu.abi", "ro.product.cpu.abilist"] + [f"ro.{partition}product.cpu.abi" for partition in PARTITIONS] + [f"ro.{partition}product.cpu.abilist" for partition in PARTITIONS]
DEVICE_IS_AB = ["ro.build.ab_update"]
DEVICE_PLATFORM = ["ro.board.platform"]
DEVICE_PIXEL_FORMAT = ["ro.minui.pixel_format"]

(
	ARCH_ARM,
	ARCH_ARM64,
	ARCH_X86,
	ARCH_X86_64,
	ARCH_UNKNOWN,
) = range(5)

ARCH_TO_STRING = {
	ARCH_ARM: "arm",
	ARCH_ARM64: "arm64",
	ARCH_X86: "x86",
	ARCH_X86_64: "x86_64",
	ARCH_UNKNOWN: "unknown",
}

# Common kernel formats based on architecture
# TODO: Directly check kernel type
KERNEL_NAMES = {
	ARCH_ARM: "zImage",
	ARCH_ARM64: "Image.gz",
	ARCH_X86: "bzImage",
	ARCH_X86_64: "bzImage",
	ARCH_UNKNOWN: "Image",
}

class DeviceInfo:
	"""
	This class is responsible for reading parse common build props needed for twrpdtgen
	by using BuildProp class.
	"""

	def __init__(self, buildprop: BuildProp):
		"""
		Parse common build props needed for twrpdtgen.
		"""
		self.buildprop = buildprop

		# Parse props
		self.codename = self.get_prop(DEVICE_CODENAME)
		self.manufacturer = self.get_prop(DEVICE_MANUFACTURER).split()[0].lower()
		self.brand = self.get_prop(DEVICE_BRAND)
		self.model = self.get_prop(DEVICE_MODEL)

		self.arch = self.parse_arch(self.get_prop(DEVICE_ARCH))
		self.arch_str = ARCH_TO_STRING[self.arch]
		self.device_has_64bit_arch = self.arch in ("arm64", "x86_64")
		self.platform = self.get_prop(DEVICE_PLATFORM, default="default")
		self.device_is_ab = bool(strtobool(self.get_prop(DEVICE_IS_AB, default="false")))
		self.device_pixel_format = self.get_prop(DEVICE_PIXEL_FORMAT, raise_exception=False)
		self.kernel_name = KERNEL_NAMES[self.arch]

	def get_prop(self, props: list, default: str = None, raise_exception: bool = True):
		for prop in props:
			prop_value = self.buildprop.get_prop(prop)
			if prop_value is not None:
				return prop_value

		if default is None and raise_exception:
			raise AssertionError(f'Property {props[0]} could not be found in build.prop')
		else:
			return default

	def parse_arch(self, arch: str):
		if arch.startswith("arm64"):
			return ARCH_ARM64
		if arch.startswith("armeabi"):
			return ARCH_ARM
		if arch.startswith("x86"):
			return ARCH_X86
		if arch.startswith("x86_64"):
			return ARCH_X86_64
		return ARCH_UNKNOWN
