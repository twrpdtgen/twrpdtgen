"""Build.prop reader class implementation"""
import re
from pathlib import Path
from typing import Pattern

DEVICE_CODENAME_RE = re.compile(r'(?:ro.product.*device=)(.*)$', re.MULTILINE)
DEVICE_MANUFACTURER_RE = re.compile(r'(?:ro.product.*manufacturer=)(.*)$', re.MULTILINE)
DEVICE_PLATFORM_RE = re.compile(r'(?:ro.board.platform=|ro.hardware.keystore=|ro.hardware.chipname=)(.*)$', re.MULTILINE)
DEVICE_BRAND_RE = re.compile(r'(?:ro.product.*brand=)(.*)$', re.MULTILINE)
DEVICE_MODEL_RE = re.compile(r'(?:ro.product.*model=)(.*)$', re.MULTILINE)
DEVICE_ARCH_RE = re.compile(r'(?:ro.product.cpu.abi=|ro.product.cpu.abilist=)(.*)$', re.MULTILINE)
DEVICE_IS_AB_RE = re.compile(r'(?:ro.build.ab_update=true)(.*)$', re.MULTILINE)

class BuildPropReader:
    """
    This class is responsible for reading build.prop files
    and extracting required information from it
    """
    # pylint: disable=too-many-instance-attributes, too-few-public-methods

    def __init__(self, file: Path):
        """
        Build.prop reader class constructor.
        :param file: build.prop file path as a Path object
        """
        self._filename = file.absolute()
        self._content = self._filename.read_text()

        # Parse props
        self.codename = self.get_prop(DEVICE_CODENAME_RE, "codename")
        self.manufacturer = self.get_prop(DEVICE_MANUFACTURER_RE, "manufacturer").lower()
        self.platform = self.get_prop(DEVICE_PLATFORM_RE, "platform")
        self.brand = self.get_prop(DEVICE_BRAND_RE, "brand")
        self.model = self.get_prop(DEVICE_MODEL_RE, "model")
        self.arch = self.parse_arch(self.get_prop(DEVICE_ARCH_RE, "arch"))
        self.device_is_ab = bool(DEVICE_IS_AB_RE.search(self._content))
        self.device_has_64bit_arch = self.arch in ("arm64", "x86_64")

    def get_prop(self, regex: Pattern, error: str) -> str:
        """
        Get a prop value from a regular expression pattern
        """
        match = regex.search(self._content)
        if match:
            return match.group(1)
        else:
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
