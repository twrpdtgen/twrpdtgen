#
# Copyright (C) 2020 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from pathlib import Path

FSTAB_LOCATIONS = [Path() / "etc" / "recovery.fstab"]
FSTAB_LOCATIONS += [Path() / dir / "etc" / "recovery.fstab"
					for dir in ["system", "vendor"]]

INIT_RC_LOCATIONS = [Path()]
INIT_RC_LOCATIONS += [Path() / dir / "etc" / "init"
					  for dir in ["system", "vendor"]]
