"""Build.prop reader class implementation"""
import re
from pathlib import Path
from typing import Union

DEVICE_CODENAME_RE = re.compile(r'(?:ro.product.device=|ro.system.device='
                                r'|ro.vendor.device=)(.*)$', re.MULTILINE)
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
    device_is_ab: bool

    def __init__(self, file):
        """
        Build.prop reader class instructor
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
        # device is AB
        _match = DEVICE_IS_AB_RE.search(self._content)
        self.device_is_ab = bool(_match)

    @staticmethod
    def _error(prop):
        """Raise and AssertionError if information couldn't be extracted."""
        raise AssertionError(f"Device {prop} could not be found in build.prop")
