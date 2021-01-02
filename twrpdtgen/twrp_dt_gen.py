#!/usr/bin/python3

# pylint: disable=too-many-locals, too-many-statements, too-many-branches

from logging import debug, info, warning, error
from pathlib import Path
from shutil import copyfile
from twrpdtgen.aik_manager import AIKManager
from twrpdtgen.info_extractors.buildprop import BuildPropReader
from twrpdtgen.info_extractors.recovery_image import RecoveryImageInfoReader
from twrpdtgen.misc import render_template
from twrpdtgen.utils.device_tree import DeviceTree
from twrpdtgen.utils.fstab import make_twrp_fstab

# Makes the linter happy
debug = debug
info = info
warning = warning
error = error

def main(recovery_image: Path, output_path: Path, is_debug=False) -> DeviceTree:
    """
    Generate a TWRP-compatible device tree from a recovery image (or a boot image if the device is A/B)

    Returns a DeviceTree object if the generation went fine, else an integer
    """
    if not recovery_image.is_file():
        raise FileNotFoundError("Specified file doesn't exist")

    aik = AIKManager(is_debug)
    aik_ramdisk_path, aik_images_path = aik.extract_recovery(recovery_image)

    debug("Getting device infos...")
    recovery_image_info = RecoveryImageInfoReader(aik_ramdisk_path, aik_images_path)
    if recovery_image_info.buildprop is None:
        raise AssertionError("Couldn't find any build.prop")
    debug("Using " + str(recovery_image_info.buildprop) + " as build.prop")
    build_prop = BuildPropReader(recovery_image_info.buildprop)
    device_tree = DeviceTree(build_prop, output_path)

    debug("Copying kernel...")
    recovery_image_info.get_kernel_name(build_prop.arch)
    if recovery_image_info.kernel is not None:
        copyfile(recovery_image_info.kernel,
                 device_tree.prebuilt_path / recovery_image_info.kernel_name)
    if recovery_image_info.dt_image is not None:
        copyfile(recovery_image_info.dt_image, device_tree.dt_image)
    if recovery_image_info.dtb_image is not None:
        copyfile(recovery_image_info.dtb_image, device_tree.dtb_image)
    if recovery_image_info.dtbo_image is not None:
        copyfile(recovery_image_info.dtbo_image, device_tree.dtbo_image)

    if Path(aik_ramdisk_path / "etc" / "twrp.fstab").is_file():
        debug("Found a TWRP fstab, copying it...")
        copyfile(aik_ramdisk_path / "etc" / "twrp.fstab", device_tree.fstab)
    elif Path(aik_ramdisk_path / "etc" / "recovery.fstab").is_file():
        debug("Generating fstab...")
        make_twrp_fstab(aik_ramdisk_path / "etc" / "recovery.fstab",
                        device_tree.fstab)
    elif Path(aik_ramdisk_path / "system" / "etc" / "recovery.fstab").is_file():
        debug("Generating fstab...")
        make_twrp_fstab(aik_ramdisk_path / "system" / "etc" / "recovery.fstab",
                        device_tree.fstab)
    else:
        raise AssertionError("fstab not found")

    for file in aik_ramdisk_path.iterdir():
        if file.name.endswith(".rc") and file != "init.rc":
            copyfile(aik_ramdisk_path / file,
                     device_tree.recovery_root_path / file.name, follow_symlinks=True)

    debug("Creating Android.mk...")
    render_template(device_tree.path, "Android.mk.jinja2", device_codename=build_prop.codename)

    debug("Creating AndroidProducts.mk...")
    render_template(device_tree.path, "AndroidProducts.mk.jinja2",
                    device_codename=build_prop.codename)

    debug("Creating BoardConfig.mk...")
    render_template(device_tree.path, "BoardConfig.mk.jinja2",
                    device_manufacturer=build_prop.manufacturer,
                    device_codename=build_prop.codename,
                    device_is_ab=build_prop.device_is_ab,
                    device_platform=build_prop.platform,
                    device_arch=build_prop.arch,
                    board_name=recovery_image_info.board_name,
                    recovery_size=recovery_image_info.recovery_size,
                    cmdline=recovery_image_info.cmdline,
                    kernel=recovery_image_info.kernel,
                    kernel_name=recovery_image_info.kernel_name,
                    dt_image=recovery_image_info.dt_image,
                    dtb_image=recovery_image_info.dtb_image,
                    dtbo_image=recovery_image_info.dtbo_image,
                    header_version=recovery_image_info.header_version,
                    base_address=recovery_image_info.base_address,
                    pagesize=recovery_image_info.pagesize,
                    ramdisk_offset=recovery_image_info.ramdisk_offset,
                    tags_offset=recovery_image_info.tags_offset,
                    ramdisk_compression=recovery_image_info.ramdisk_compression,
                    flash_block_size=str(int(recovery_image_info.pagesize) * 64))

    debug("Creating device.mk...")
    render_template(device_tree.path, "device.mk.jinja2",
                    device_codename=build_prop.codename,
                    device_manufacturer=build_prop.manufacturer,
                    device_platform=build_prop.platform,
                    device_is_ab=build_prop.device_is_ab)

    debug(f"Creating omni_{build_prop.codename}.mk...")
    render_template(device_tree.path, "omni.mk.jinja2", out_file=f"omni_{build_prop.codename}.mk",
                    device_codename=build_prop.codename,
                    device_manufacturer=build_prop.manufacturer,
                    device_brand=build_prop.brand,
                    device_model=build_prop.model,
                    device_has_64bit_arch=build_prop.device_has_64bit_arch)

    debug("Creating vendorsetup.sh...")
    render_template(device_tree.path, "vendorsetup.sh.jinja2", device_codename=build_prop.codename)

    git_config_reader = device_tree.git_repo.config_reader()
    git_config_writer = device_tree.git_repo.config_writer()
    try:
        git_global_email, git_global_name = git_config_reader.get_value('user', 'email'), git_config_reader.get_value('user', 'name')
    except:
        git_global_email, git_global_name = None, None
    if git_global_email is None or git_global_name is None:
        git_config_writer.set_value('user', 'email', 'barezzisebastiano@gmail.com')
        git_config_writer.set_value('user', 'name', 'Sebastiano Barezzi')
    device_tree.git_repo.index.add(["*"])
    commit_message = render_template(None, "commit_message.jinja2", to_file=False,
                                     device_codename=build_prop.codename,
                                     device_arch=build_prop.arch,
                                     device_manufacturer=build_prop.manufacturer,
                                     device_brand=build_prop.brand,
                                     device_model=build_prop.model)
    device_tree.git_repo.index.commit(commit_message)

    # Cleanup
    aik.cleanup()

    return device_tree
