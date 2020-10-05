#!/usr/bin/python3

# pylint: disable=too-many-locals, too-many-statements, too-many-branches

from pathlib import Path
from shutil import copyfile, rmtree
from sys import argv, exit as sys_exit

from git import Repo
from git.exc import InvalidGitRepositoryError

from twrpdtgen import __version__ as version, aik_path
from twrpdtgen import current_path, working_path
from twrpdtgen.aik_manager import AIKManager
from twrpdtgen.info_readers.buildprop_reader import BuildPropReader
from twrpdtgen.misc import error, make_twrp_fstab, open_file_and_read, \
    print_help, render_template

TWRPDTGEN_REPO = None
try:
    TWRPDTGEN_REPO = Repo(current_path)
except InvalidGitRepositoryError:
    error("Please clone the script with Git instead of downloading it as a zip")
    sys_exit()
last_commit = TWRPDTGEN_REPO.head.object.hexsha[:7]


def main():
    print(f"TWRP device tree generator\n"
          "Python Edition\n"
          f"Version {version}\n")
    recovery_image = Path()
    try:
        recovery_image = Path(argv[1])
    except IndexError:
        error("Recovery image not provided")
        print_help()
        sys_exit()

    if not recovery_image.is_file():
        error("Recovery image doesn't exist")
        print_help()
        sys_exit()

    aik = AIKManager(aik_path)
    aik_ramdisk_path, aik_images_path = aik.extract_recovery(recovery_image)

    print("Getting device infos...")
    build_prop = BuildPropReader(aik_ramdisk_path / "default.prop")

    aik_images_path_base = str(aik_images_path / "recovery.img-")
    device_tree_path = working_path / build_prop.manufacturer / build_prop.codename
    device_tree_prebuilt_path = device_tree_path / "prebuilt"
    device_tree_recovery_root_path = device_tree_path / "recovery" / "root"
    # device_tree_files = ["Android.mk", "AndroidProducts.mk", "BoardConfig.mk", "device.mk",
    #                      "omni_" + device_codename + ".mk", "vendorsetup.sh"]

    device_have_kernel = Path(aik_images_path_base + "zImage").is_file()
    device_have_dt_image = Path(aik_images_path_base + "dt").is_file()
    device_have_dtb_image = Path(aik_images_path_base + "dtb").is_file()
    device_have_dtbo_image = Path(aik_images_path_base + "dtbo").is_file()
    device_base_address = open_file_and_read(aik_images_path_base + "base")
    device_board_name = open_file_and_read(aik_images_path_base + "board")
    device_cmdline = open_file_and_read(aik_images_path_base + "cmdline")
    # device_hash_type = open_file_and_read(aik_images_path_base + "hashtype")
    device_header_version = open_file_and_read(aik_images_path_base + "header_version")
    # device_image_type = open_file_and_read(aik_images_path_base + "imgtype")
    # device_kernel_offset = open_file_and_read(aik_images_path_base + "kernel_offset")
    device_recovery_size = open_file_and_read(aik_images_path_base + "origsize")
    # device_recovery_sp = open_file_and_read(aik_images_path_base + "os_patch_level")
    # device_recovery_version = open_file_and_read(aik_images_path_base + "os_version")
    device_pagesize = open_file_and_read(aik_images_path_base + "pagesize")
    device_ramdisk_compression = open_file_and_read(aik_images_path_base + "ramdiskcomp")
    device_ramdisk_offset = open_file_and_read(aik_images_path_base + "ramdisk_offset")
    # device_second_offset = open_file_and_read(aik_images_path_base + "second_offset")
    device_tags_offset = open_file_and_read(aik_images_path_base + "tags_offset")

    print("Creating device tree folders...")
    if device_tree_path.is_dir():
        rmtree(device_tree_path, ignore_errors=True)
    device_tree_path.mkdir(parents=True)
    device_tree_prebuilt_path.mkdir(parents=True)
    device_tree_recovery_root_path.mkdir(parents=True)

    print("Copying kernel...")
    device_kernel_name = ""
    if device_have_kernel:
        if build_prop.arch == "arm":
            device_kernel_name = "zImage"
        elif build_prop.arch == "arm64":
            device_kernel_name = "Image.gz"
        elif build_prop.arch in ("x86", "x86_64"):
            device_kernel_name = "bzImage"
        else:
            device_kernel_name = "zImage"
        if build_prop.arch in ("arm", "arm64") and (
                not device_have_dt_image and not device_have_dtb_image):
            device_kernel_name += "-dtb"
        copyfile(aik_images_path_base + "zImage", device_tree_prebuilt_path / device_kernel_name)
    if device_have_dt_image:
        copyfile(aik_images_path_base + "dt", device_tree_prebuilt_path / "dt.img")
    if device_have_dtb_image:
        copyfile(aik_images_path_base + "dtb", device_tree_prebuilt_path / "dtb.img")
    if device_have_dtbo_image:
        copyfile(aik_images_path_base + "dtbo", device_tree_prebuilt_path / "dtbo.img")

    if Path(aik_ramdisk_path / "etc" / "twrp.fstab").is_file():
        print("Found a TWRP fstab, copying it...")
        copyfile(aik_ramdisk_path / "etc" / "twrp.fstab", device_tree_path / "recovery.fstab")
    else:
        print("Generating fstab...")
        make_twrp_fstab(aik_ramdisk_path / "etc" / "recovery.fstab",
                        device_tree_path / "recovery.fstab")

    for file in aik_ramdisk_path.iterdir():
        if file.name.endswith(".rc") and file != "init.rc":
            copyfile(aik_ramdisk_path / file,
                     device_tree_recovery_root_path / file.name, follow_symlinks=True)

    print("Creating Android.mk...")
    render_template(device_tree_path, "Android.mk.jinja2", device_codename=build_prop.codename)

    print("Creating AndroidProducts.mk...")
    render_template(device_tree_path, "AndroidProducts.mk.jinja2", device_codename=build_prop.codename)

    print("Creating BoardConfig.mk...")
    render_template(device_tree_path, "BoardConfig.mk.jinja2",
                    device_manufacturer=build_prop.manufacturer,
                    device_codename=build_prop.codename,
                    device_is_ab=build_prop.device_is_ab,
                    device_platform=build_prop.platform,
                    device_arch=build_prop.arch,
                    device_board_name=device_board_name,
                    device_recovery_size=device_recovery_size,
                    device_cmdline=device_cmdline,
                    device_have_kernel=device_have_kernel,
                    device_kernel_name=device_kernel_name,
                    device_have_dt_image=device_have_dt_image,
                    device_have_dtb_image=device_have_dtb_image,
                    device_have_dtbo_image=device_have_dtbo_image,
                    device_header_version=device_header_version,
                    device_base_address=device_base_address,
                    device_pagesize=device_pagesize,
                    device_ramdisk_offset=device_ramdisk_offset,
                    device_tags_offset=device_tags_offset,
                    device_ramdisk_compression=device_ramdisk_compression,
                    flash_block_size=str(int(device_pagesize) * 64)
                    )

    print("Creating device.mk...")
    render_template(device_tree_path, "device.mk.jinja2",
                    device_codename=build_prop.codename,
                    device_manufacturer=build_prop.manufacturer,
                    device_platform=build_prop.platform,
                    device_is_ab=build_prop.device_is_ab)

    print(f"Creating omni_{build_prop.codename}.mk...")
    render_template(device_tree_path, "omni.mk.jinja2", out_file=f"omni_{build_prop.codename}.mk",
                    device_codename=build_prop.codename,
                    device_manufacturer=build_prop.manufacturer,
                    device_brand=build_prop.brand,
                    device_model=build_prop.model,
                    device_has_64bit_arch=build_prop.device_has_64bit_arch
                    )

    print("Creating vendorsetup.sh...")
    render_template(device_tree_path, "vendorsetup.sh.jinja2", device_codename=build_prop.codename)

    dt_repo = Repo.init(device_tree_path)
    with dt_repo.config_writer() as git_config:
        git_config.set_value('user', 'email', 'barezzisebastiano@gmail.com')
        git_config.set_value('user', 'name', 'Sebastiano Barezzi')
    dt_repo.index.add(["*"])
    commit_message = render_template(None, "commit_message.jinja2", to_file=False,
                                     device_codename=build_prop.codename,
                                     device_arch=build_prop.arch,
                                     device_manufacturer=build_prop.manufacturer,
                                     device_brand=build_prop.brand,
                                     device_model=build_prop.model,
                                     last_commit=last_commit)
    dt_repo.index.commit(commit_message)
    print(f"\nDone! You can find the device tree in {str(device_tree_path)}")
