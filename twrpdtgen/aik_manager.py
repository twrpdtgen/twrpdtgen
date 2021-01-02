from pathlib import Path
from platform import system
from shutil import copyfile, rmtree
from subprocess import Popen, PIPE, call
from tempfile import TemporaryDirectory
from typing import Tuple, Union

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
            self._path = Path(self.tempdir.name)
        else:
            self._path = current_path / "extract"
        if self._path.is_dir():
            rmtree(self._path, ignore_errors=False, onerror=handle_remove_readonly)

        info("Cloning AIK...")
        if system() == "Linux":
            Repo.clone_from("https://github.com/SebaUbuntu/AIK-Linux-mirror", self._path)
        elif system() == "Windows":
            Repo.clone_from("https://github.com/SebaUbuntu/AIK-Windows-mirror", self._path)

    def extract_recovery(self, recovery_image: Union[Path, str]) -> Tuple[Path, Path]:
        """
        Extract a custom recovery image using AIK.
        :param recovery_image: recovery image string or path object
        :return: extracted ramdisk and split image tuple of path objects
        """
        new_recovery_image = self._path / "recovery.img"
        copyfile(recovery_image, new_recovery_image)
        # TODO Check if AIK extract is successful
        if system() == "Linux":
            aik_process = Popen([self._path / "unpackimg.sh", "--nosudo", new_recovery_image],
                                stdout=PIPE, stderr=PIPE, universal_newlines=True)
            _, _ = aik_process.communicate()
        elif system() == "Windows":
            call([self._path / "unpackimg.bat", new_recovery_image])
        else:
            raise NotImplementedError(f"{system()} is not supported!")
        return self._path / "ramdisk", self._path / "split_img"

    def cleanup(self):
        if not self.is_debug:
            self.tempdir.cleanup()
