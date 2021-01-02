#!/usr/bin/python3

from argparse import ArgumentParser
from pathlib import Path
from twrpdtgen import __version__ as version, current_path
from twrpdtgen.twrp_dt_gen import main
from twrpdtgen.utils.logging import setup_logging

if __name__ == '__main__':
    print(f"TWRP device tree generator\n"
      "Python Edition\n"
      f"Version {version}\n")

    parser = ArgumentParser(prog='python3 -m twrpdtgen')
    parser.add_argument("recovery_image", type=Path,
                        help="path to a recovery image (or boot image if the device is A/B)")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="Enable debugging logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    dt = main(args.recovery_image, current_path / "working")
    if type(dt) is not int:
        print(f"\nDone! You can find the device tree in {str(dt.path)}")
    else:
        print("\nAn error has occurred")
