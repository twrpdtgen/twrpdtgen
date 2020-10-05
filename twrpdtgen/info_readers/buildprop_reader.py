"""Build.prop reader class implementation"""
import re
from pathlib import Path
from typing import Union

DEVICE_CODENAME_RE = re.compile(r'(?:ro.product.device=|ro.system.device='
                                r'|ro.vendor.device=|ro.product.system.device=)(.*)$', re.MULTILINE)
DEVICE_MANUFACTURER_RE = re.compile(
    r'(?:ro.product.manufacturer=|ro.product.system.manufacturer='
    r'|ro.product.vendor.manufacturer=)(.*)$',
    re.MULTILINE)
DEVICE_PLATFORM_RE = re.compile(r'(?:ro.board.platform='
                                r'|ro.hardware.keystore=)(.*)$', re.MULTILINE)
DEVICE_BRAND_RE = re.compile(
    r'(?:ro.product.brand=|ro.product.system.brand='
    r'|ro.product.vendor.brand=)(.*)$', re.MULTILINE)
DEVICE_MODEL_RE = re.compile(
    r'(?:ro.product.model=|ro.product.system.model='
    r'|ro.product.vendor.model=)(.*)$', re.MULTILINE)
DEVICE_ARCH_RE = re.compile(r'(?:ro.product.cpu.abi=|ro.product.cpu.abilist=)(.*)$', re.MULTILINE)
DEVICE_IS_AB_RE = re.compile(r'(?:ro.build.ab_update=true)(.*)$', re.MULTILINE)


class BuildPropReader:
    """
    This class is responsible for reading build.prop files
     and extracting required information from it"""
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    _filename: Union[Path, str]
    _content: str
    codename: str
    manufacturer: str
    platform: str
    brand: str
    model: str
    arch: str
    device_is_ab: bool
    device_has_64bit_arch: bool

    def __init__(self, file):
        """
        Build.prop reader class constructor.
        :param file: build.prop file path as a string or Path object
        """
        self._filename = Path(file).absolute()
        self._content = self._filename.read_text()
        # codename
        _match = DEVICE_CODENAME_RE.search(self._content)
        if _match:
            self.codename = _match.group(1)
        else:
            self._error("codename")
        # manufacturer
        _match = DEVICE_MANUFACTURER_RE.search(self._content)
        if _match:
            self.manufacturer = _match.group(1).lower()
        else:
            self._error("manufacturer")
        # platform
        _match = DEVICE_PLATFORM_RE.search(self._content)
        if _match:
            self.platform = _match.group(1)
        else:
            self._error("platform")
        # brand
        _match = DEVICE_BRAND_RE.search(self._content)
        if _match:
            self.brand = _match.group(1)
        else:
            self._error("brand")
        # model
        _match = DEVICE_MODEL_RE.search(self._content)
        if _match:
            self.model = _match.group(1)
        else:
            self._error("model")
        # arch
        _match = DEVICE_ARCH_RE.search(self._content)
        if _match:
            self.arch = self.parse_arch(_match.group(1))
        else:
            self._error("architecture")
        # device is AB
        _match = DEVICE_IS_AB_RE.search(self._content)
        self.device_is_ab = bool(_match)
        self.device_has_64bit_arch = self.arch in ("arm64", "x86_64")

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

    @staticmethod
    def _error(prop):
        """Raise and AssertionError if information couldn't be extracted."""
        raise AssertionError(f"Device {prop} could not be found in build.prop")
