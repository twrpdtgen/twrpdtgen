#!/usr/bin/python3

from argparse import ArgumentParser
from pathlib import Path
from twrpdtgen import __version__ as version, current_path
from twrpdtgen.device_tree import DeviceTree
from twrpdtgen.utils.logging import setup_logging

if __name__ == '__main__':
	print(f"TWRP device tree generator\n"
		  f"Version {version}\n")

	parser = ArgumentParser(prog='python3 -m twrpdtgen')

	# Main DeviceTree arguments
	parser.add_argument("recovery_image", type=Path, nargs='?', default=None,
						help="path to a recovery image (or boot image if the device is A/B)")
	parser.add_argument("-o", "--output", type=Path, default=current_path / "output",
						help="custom output folder")

	# Optional DeviceTree arguments
	parser.add_argument("-k", "--keep-aik", action='store_true',
						help="keep AIK after the generation")
	parser.add_argument("--no-git", action='store_true',
						help="don't create a git repo after the generation")

	# Huawei DeviceTree arguments
	parser.add_argument("--huawei", action='store_true',
						help="Huawei mode (split kernel, ramdisk and vendor)")
	parser.add_argument("--recovery_kernel", type=Path, default=None,
						help="path to a recovery_kernel file (huawei mode only)")
	parser.add_argument("--recovery_ramdisk", type=Path, default=None,
						help="path to a recovery_ramdisk file (huawei mode only)")
	parser.add_argument("--recovery_vendor", type=Path, default=None,
						help="path to a recovery_vendor file (huawei mode only)")

	# Logging
	parser.add_argument("-v", "--verbose", action='store_true',
						help="enable debugging logging")

	args = parser.parse_args()

	if not args.huawei and args.recovery_image is None:
		parser.error("the following arguments are required: recovery_image")
	elif args.huawei:
		if args.recovery_kernel is None or args.recovery_ramdisk is None or args.recovery_vendor is None:
			parser.error("the following arguments are required:" 
						 " --recovery_kernel, --recovery_ramdisk, --recovery_vendor")

	setup_logging(args.verbose)

	dt = DeviceTree(args.output, recovery_image=args.recovery_image,
					no_git=args.no_git, keep_aik=args.keep_aik,
					huawei=args.huawei, recovery_kernel=args.recovery_kernel,
					recovery_ramdisk=args.recovery_ramdisk, recovery_vendor=args.recovery_vendor)

	print(f"\nDone! You can find the device tree in {str(dt.path)}")
