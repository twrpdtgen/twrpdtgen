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
from twrpdtgen.info_extractors.buildprop import BuildPropReader
from twrpdtgen.info_extractors.recovery_image import RecoveryImageInfoReader
from twrpdtgen.misc import error, make_twrp_fstab, print_help, render_template


def self_repo_check() -> str:
    """
    Check tool repository before starting
    :return: last local commit
    """
    try:
        twrpdtgen_repo = Repo(current_path)
        return twrpdtgen_repo.head.object.hexsha[:7]
    except InvalidGitRepositoryError:
        error("Please clone the script with Git instead of downloading it as a zip")
        sys_exit()


def main():
    # TODO switch to ArgsParser for dealing with args
    print(f"TWRP device tree generator\n"
          "Python Edition\n"
          f"Version {version}\n")
    last_commit = self_repo_check()
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
    recovery_image_info = RecoveryImageInfoReader(aik_ramdisk_path, aik_images_path)

    device_tree_path = working_path / build_prop.manufacturer / build_prop.codename
    device_tree_prebuilt_path = device_tree_path / "prebuilt"
    device_tree_recovery_root_path = device_tree_path / "recovery" / "root"

    print("Creating device tree folders...")
    # TODO refactor to Device Tree Manager class
    if device_tree_path.is_dir():
        rmtree(device_tree_path, ignore_errors=True)
    device_tree_path.mkdir(parents=True)
    device_tree_prebuilt_path.mkdir(parents=True)
    device_tree_recovery_root_path.mkdir(parents=True)

    print("Copying kernel...")
    recovery_image_info.get_kernel_name(build_prop.arch)
    if recovery_image_info.kernel_name:
        copyfile(recovery_image_info.aik_images_path_base + "zImage",
                 device_tree_prebuilt_path / recovery_image_info.kernel_name)
    if recovery_image_info.has_dt_image:
        copyfile(recovery_image_info.aik_images_path_base + "dt",
                 device_tree_prebuilt_path / "dt.img")
    if recovery_image_info.has_dtb_image:
        copyfile(recovery_image_info.aik_images_path_base + "dtb",
                 device_tree_prebuilt_path / "dtb.img")
    if recovery_image_info.has_dtbo_image:
        copyfile(recovery_image_info.aik_images_path_base + "dtbo",
                 device_tree_prebuilt_path / "dtbo.img")

    if Path(aik_ramdisk_path / "etc" / "twrp.fstab").is_file():
        print("Found a TWRP fstab, copying it...")
        copyfile(aik_ramdisk_path / "etc" / "twrp.fstab", device_tree_path / "recovery.fstab")
    else:
        print("Generating fstab...")
        # TODO refactor to better fstab generator
        make_twrp_fstab(aik_ramdisk_path / "etc" / "recovery.fstab",
                        device_tree_path / "recovery.fstab")

    for file in aik_ramdisk_path.iterdir():
        if file.name.endswith(".rc") and file != "init.rc":
            copyfile(aik_ramdisk_path / file,
                     device_tree_recovery_root_path / file.name, follow_symlinks=True)

    print("Creating Android.mk...")
    render_template(device_tree_path, "Android.mk.jinja2", device_codename=build_prop.codename)

    print("Creating AndroidProducts.mk...")
    render_template(device_tree_path, "AndroidProducts.mk.jinja2",
                    device_codename=build_prop.codename)

    print("Creating BoardConfig.mk...")
    render_template(device_tree_path, "BoardConfig.mk.jinja2",
                    device_manufacturer=build_prop.manufacturer,
                    device_codename=build_prop.codename,
                    device_is_ab=build_prop.device_is_ab,
                    device_platform=build_prop.platform,
                    device_arch=build_prop.arch,
                    board_name=recovery_image_info.board_name,
                    recovery_size=recovery_image_info.recovery_size,
                    cmdline=recovery_image_info.cmdline,
                    has_kernel=recovery_image_info.has_kernel,
                    kernel_name=recovery_image_info.kernel_name,
                    has_dt_image=recovery_image_info.has_dt_image,
                    has_dtb_image=recovery_image_info.has_dtb_image,
                    has_dtbo_image=recovery_image_info.has_dtbo_image,
                    header_version=recovery_image_info.header_version,
                    base_address=recovery_image_info.base_address,
                    pagesize=recovery_image_info.pagesize,
                    ramdisk_offset=recovery_image_info.ramdisk_offset,
                    tags_offset=recovery_image_info.tags_offset,
                    ramdisk_compression=recovery_image_info.ramdisk_compression,
                    flash_block_size=str(int(recovery_image_info.pagesize) * 64)
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

    # TODO move to Device Tree Manager
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
