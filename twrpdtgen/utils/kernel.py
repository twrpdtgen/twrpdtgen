#
# Copyright (C) 2020 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Common kernel formats based on architecture
# TODO: Directly check kernel type
kernel_names = {
	"arm": "zImage",
	"arm64": "Image.gz",
	"x86": "bzImage",
	"x86_64": "bzImage"
}

def get_kernel_name(arch: str) -> str:
	return kernel_names.get(arch, "zImage")
