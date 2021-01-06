#!/usr/bin/python3

from argparse import ArgumentParser
from pathlib import Path
from twrpdtgen import __version__ as version, current_path
from twrpdtgen.twrp_dt_gen import generate_device_tree
from twrpdtgen.utils.logging import setup_logging

if __name__ == '__main__':
	print(f"TWRP device tree generator\n"
		  f"Version {version}\n")

	parser = ArgumentParser(prog='python3 -m twrpdtgen')
	parser.add_argument("recovery_image", type=Path,
						help="path to a recovery image (or boot image if the device is A/B)")
	parser.add_argument("-o", "--output", type=Path, default=current_path / "output",
						help="custom output folder")
	parser.add_argument("--no-git", action='store_true',
						help="don't create a git repo after the generation")
	parser.add_argument("-v", "--verbose", action='store_true',
						help="enable debugging logging")
	parser.add_argument("-k", "--keep-aik", action='store_true',
						help="keep AIK after the generation")
	args = parser.parse_args()

	setup_logging(args.verbose)

	dt = generate_device_tree(args.recovery_image, args.output, no_git=args.no_git, keep_aik=args.keep_aik)
	print(f"\nDone! You can find the device tree in {str(dt.path)}")
