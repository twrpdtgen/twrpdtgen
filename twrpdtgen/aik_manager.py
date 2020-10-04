"""AIK Manager class"""
from pathlib import Path
from platform import system
from shutil import rmtree, copyfile
from subprocess import Popen, PIPE, call
from typing import Union

from git import Repo

from twrpdtgen.misc import handle_remove_readonly


class AIKManager:
    """
    This class is responsible for dealing with AIK tasks
     such as cloning, updating, and extracting recovery images.
    """

    def __init__(self, aik_path: Path):
        """
        AIKManager constructor method
        First, check if AIK path exists, if so, update AIK, else clone AIK.

        :param aik_path: Path object of AIK directory
        """
        self._path = aik_path
        if aik_path.exists() and aik_path.is_dir():
            self.update_aik()
        else:
            self.clone_aik()

    def update_aik(self):
        """Update AIK using git if newer version is available."""
        aik = Repo(self._path)
        current_commit = aik.head.commit.hexsha
        last_upstream_commit = aik.remote().fetch()[0].commit.hexsha
        if current_commit != last_upstream_commit:
            print(f"Updating AIK to {last_upstream_commit[:7]}")
            rmtree(self._path, ignore_errors=False, onerror=handle_remove_readonly)
            self.clone_aik()
        else:
            print("AIK is up-to-date")

    def clone_aik(self):
        """Clone AIK using git clone command."""
        print("Cloning AIK...")
        if system() == "Linux":
            Repo.clone_from("https://github.com/SebaUbuntu/AIK-Linux-mirror", self._path)
        elif system() == "Windows":
            Repo.clone_from("https://github.com/SebaUbuntu/AIK-Windows-mirror", self._path)

    def extract_recovery(self, recovery_image: Union[Path, str]) -> (Path, Path):
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
