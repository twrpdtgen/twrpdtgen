from argparse import ArgumentParser
from pathlib import Path
from twrpdtgen import __version__ as version, current_path
from twrpdtgen.devicetree import DeviceTree
from twrpdtgen.utils.logging import setup_logging


print(f"TWRP device tree generator\n"
	  f"Version {version}\n")

parser = ArgumentParser(prog='python3 -m twrpdtgen')

# Main DeviceTree arguments
parser.add_argument("image", type=Path,
						help="path to an image (recovery image or boot image if the device is A/B)")
parser.add_argument("-o", "--output", type=Path, default=current_path / "output",
						help="custom output folder")

# Optional DeviceTree arguments
parser.add_argument("--git", action='store_true',
					help="create a git repo after the generation")

# Logging
parser.add_argument("-d", "--debug", action='store_true',
					help="enable debugging features")

args = parser.parse_args()

setup_logging(args.debug)

device_tree = DeviceTree(image=args.image, debug=args.debug)
folder = device_tree.dump_to_folder(args.output, git=args.git)

print(f"\nDone! You can find the device tree in {folder}")
