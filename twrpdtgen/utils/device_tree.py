#
# Copyright (C) 2020 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from git import Repo
from pathlib import Path
from shutil import rmtree

class DeviceTree:
    """
    A class representing a device tree
    """
    def __init__(self, path: Path) -> None:
        self.path = path
        self.prebuilt_path = self.path / "prebuilt"
        self.recovery_root_path = self.path / "recovery" / "root"

        print("Creating device tree folders...")
        if self.path.is_dir():
            rmtree(self.path, ignore_errors=True)
        self.path.mkdir(parents=True)
        self.prebuilt_path.mkdir(parents=True)
        self.recovery_root_path.mkdir(parents=True)

        self.git_repo = Repo.init(self.path)
        self.fstab = self.path / "recovery.fstab"
        self.dt_image = self.prebuilt_path / "dt.img"
        self.dtb_image = self.prebuilt_path / "dtb.img"
        self.dtbo_image = self.prebuilt_path / "dtbo.img"
