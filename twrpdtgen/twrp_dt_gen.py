from logging import debug, info, warning, error
from pathlib import Path
from twrpdtgen.utils.device_tree import DeviceTree

# Makes the linter happy
debug = debug
info = info
warning = warning
error = error

def generate_device_tree(recovery_image: Path, output_path: Path, no_git=False, keep_aik=False) -> DeviceTree:
	"""
	Generate a TWRP-compatible device tree from a recovery image (or a boot image if the device is A/B)

	Returns a DeviceTree object if the generation went fine, else an integer
	"""

	device_tree = DeviceTree(recovery_image, output_path,
							 no_git=no_git, keep_aik=keep_aik)

	return device_tree
