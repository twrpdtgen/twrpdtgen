#!/usr/bin/python3

from argparse import ArgumentParser
from pathlib import Path
from twrpdtgen import current_path
from twrpdtgen.twrp_dt_gen import main

if __name__ == '__main__':
    parser = ArgumentParser(prog='python3 -m twrpdtgen')
    parser.add_argument("recovery_image", type=Path,
                        help="path to a recovery image (or boot image if the device is A/B)")
    args = parser.parse_args()

    main(args.recovery_image, current_path / "working")
