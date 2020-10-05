"""Device info reader class implementation"""

from pathlib import Path
from typing import Union


class RecoveryImageInfoReader:
    """This class is responsible for reading device information from ramdisk"""
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    aik_ramdisk_path: Union[Path, str]
    aik_images_path: Union[Path, str]

    def __init__(self, aik_ramdisk_path: Union[Path, str],
                 aik_images_path: Union[Path, str]):
        """
        Device info reader class constructor
        :param aik_ramdisk_path: Extracted ramdisk path as a string or path object
        :param aik_images_path: Extracted images path as a string or path object
        """
        self.aik_ramdisk_path = aik_ramdisk_path
        self.aik_images_path = aik_images_path
        self.aik_images_path_base = str(aik_images_path / "recovery.img-")
        self.has_kernel = Path(self.aik_images_path_base + "zImage").is_file()
        self.has_dt_image = Path(self.aik_images_path_base + "dt").is_file()
        self.has_dtb_image = Path(self.aik_images_path_base + "dtb").is_file()
        self.has_dtbo_image = Path(self.aik_images_path_base + "dtbo").is_file()
        self.base_address = self.read_recovery_file(Path(self.aik_images_path_base + "base"))
        self.board_name = self.read_recovery_file(Path(self.aik_images_path_base + "board"))
        self.cmdline = self.read_recovery_file(Path(self.aik_images_path_base + "cmdline"))
        # self.device_hash_type = self.read_from_file(Path(aik_images_path_base + "hashtype"))
        header_version = Path(self.aik_images_path_base + "header_version")
        self.header_version = self.read_recovery_file(header_version) if header_version.exists() else "0"
        # self.device_image_type = self.read_from_file(
        # Path(aik_images_path_base + "imgtype"))
        # self.device_kernel_offset = self.read_from_file(
        # Path(aik_images_path_base + "kernel_offset"))
        self.recovery_size = self.read_recovery_file(
            Path(self.aik_images_path_base + "origsize"))
        # self.device_recovery_sp = self.read_from_file(
        # Path(aik_images_path_base + "os_patch_level"))
        # self.device_recovery_version = self.read_from_file(
        # Path(aik_images_path_base + "os_version"))
        self.pagesize = self.read_recovery_file(Path(self.aik_images_path_base + "pagesize"))
        self.ramdisk_compression = self.read_recovery_file(
            Path(self.aik_images_path_base + "ramdiskcomp"))
        self.ramdisk_offset = self.read_recovery_file(
            Path(self.aik_images_path_base + "ramdisk_offset"))
        # self.device_second_offset = self.read_from_file(
        # Path(aik_images_path_base + "second_offset"))
        self.tags_offset = self.read_recovery_file(
            Path(self.aik_images_path_base + "tags_offset"))
        self.kernel_name = ''

    @staticmethod
    def read_recovery_file(file: Path) -> str:
        """
        Read file contents
        :param file: file as a Path object
        :return: string of the first line of the file contents
        """
        return file.read_text().splitlines()[0]

    def get_kernel_name(self, arch: str) -> str:
        """
        Get kernel name of the device
        :param arch: device architecture information from build.prop
        :return: string of the kernel name
        """
        kernel_names = {
            "arm": "zImage",
            "arm64": "Image.gz",
            "x86": "bzImage",
            "x86_64": "bzImage"
        }
        if self.has_kernel:
            try:
                kernel_name = kernel_names[arch]
            except KeyError:
                kernel_name = "zImage"
            if arch in ("arm", "arm64") and (
                    not self.has_dt_image and not self.has_dtb_image):
                kernel_name += "-dtb"
            self.kernel_name = kernel_name
            return kernel_name
        return ""
