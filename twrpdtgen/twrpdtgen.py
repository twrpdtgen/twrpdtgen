#!/usr/bin/python3

# pylint: disable=too-many-locals, too-many-statements, too-many-branches

from pathlib import Path
from platform import system
from shutil import copyfile, rmtree
from stat import S_IWRITE
from subprocess import call, Popen, PIPE
from sys import argv, exit as sys_exit

from git import Repo
from git.exc import InvalidGitRepositoryError

from twrpdtgen import __version__ as version
from twrpdtgen import current_path, aik_path, aik_images_path, aik_ramdisk_path, working_path
from twrpdtgen.misc import error, get_device_arch, \
    make_twrp_fstab, open_file_and_read, print_help, render_template

TWRPDTGEN_REPO = None
try:
    TWRPDTGEN_REPO = Repo(current_path)
except InvalidGitRepositoryError:
    error("Please clone the script with Git instead of downloading it as a zip")
    sys_exit()
last_commit = TWRPDTGEN_REPO.head.object.hexsha[:7]


def clone_aik():
    print("Cloning AIK...")
    if system() == "Linux":
        Repo.clone_from("https://github.com/SebaUbuntu/AIK-Linux-mirror", aik_path)
    elif system() == "Windows":
        Repo.clone_from("https://github.com/SebaUbuntu/AIK-Windows-mirror", aik_path)


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

    def handle_remove_readonly(func, path, _):
        Path(path).chmod(S_IWRITE)
        func(path)

    if aik_path.exists() and aik_path.is_dir():
        aik = Repo(aik_path)
        current_commit = aik.remote().fetch()[0].commit.hexsha
        last_upstream_commit = aik.remote().fetch()[0].commit.hexsha
        if current_commit != last_upstream_commit:
            print(f"Updating AIK to {last_upstream_commit[:7]}")
            rmtree(aik_path, ignore_errors=False, onerror=handle_remove_readonly)
            clone_aik()
        else:
            print("AIK is up-to-date")
    else:
        clone_aik()

    print("Extracting recovery image...")
    new_recovery_image = aik_path / "recovery.img"
    copyfile(recovery_image, new_recovery_image)
    if system() == "Linux":
        aik_process = Popen([aik_path / "unpackimg.sh", "--nosudo", new_recovery_image],
                            stdout=PIPE, stderr=PIPE, universal_newlines=True)
        _, _ = aik_process.communicate()
    elif system() == "Windows":
        call([aik_path / "unpackimg.bat", new_recovery_image])

    print("Getting device infos...")
    arch_binary = None
    if Path(aik_ramdisk_path / "sbin" / "recovery").is_file():
        arch_binary = aik_ramdisk_path / "sbin" / "recovery"
    elif Path(aik_ramdisk_path / "sbin" / "setlockstate").is_file():
        arch_binary = aik_ramdisk_path / "sbin" / "setlockstate"
    elif Path(aik_ramdisk_path / "init").is_file():
        arch_binary = aik_ramdisk_path / "init"
    else:
        error("No expected binary has been found")
        sys_exit()

    device_codename = ""
    device_manufacturer = ""
    device_platform = ""
    device_brand = ""
    device_model = ""
    device_is_ab = False
    with open(aik_ramdisk_path / "prop.default", "r") as props:
        lines = props.read()
        for line in lines.splitlines():
            if line.startswith("ro.product.device=") \
                    or line.startswith("ro.product.system.device=") \
                    or line.startswith("ro.product.vendor.device="):
                device_codename = line.rpartition('=')[2]
            elif line.startswith("ro.product.manufacturer=") or line.startswith(
                    "ro.product.system.manufacturer=") \
                    or line.startswith("ro.product.vendor.manufacturer="):
                device_manufacturer = line.rpartition('=')[2]
                device_manufacturer = device_manufacturer.lower()
            elif line.startswith("ro.board.platform=") or line.startswith("ro.hardware.keystore="):
                device_platform = line.rpartition('=')[2]
            elif line.startswith("ro.product.brand=") \
                    or line.startswith("ro.product.system.brand=") \
                    or line.startswith("ro.product.vendor.brand="):
                device_brand = line.rpartition('=')[2]
            elif line.startswith("ro.product.model=") \
                    or line.startswith("ro.product.system.model=") \
                    or line.startswith("ro.product.vendor.model="):
                device_model = line.rpartition('=')[2]
            elif line == "ro.build.ab_update=true":
                device_is_ab = True
        props.close()

    if device_codename == "":
        error("Device codename not found on build.prop")
        sys_exit()
    if device_manufacturer == "":
        error("Device manufacturer not found on build.prop")
        sys_exit()
    if device_platform == "":
        error("Device platform not found on build.prop")
        sys_exit()
    if device_brand == "":
        error("Device brand not found on build.prop")
        sys_exit()
    if device_model == "":
        error("Device model not found on build.prop")
        sys_exit()

    aik_images_path_base = str(aik_images_path / "recovery.img-")
    device_tree_path = working_path / device_manufacturer / device_codename
    device_tree_prebuilt_path = device_tree_path / "prebuilt"
    device_tree_recovery_root_path = device_tree_path / "recovery" / "root"
    # device_tree_files = ["Android.mk", "AndroidProducts.mk", "BoardConfig.mk", "device.mk",
    #                      "omni_" + device_codename + ".mk", "vendorsetup.sh"]

    device_arch = get_device_arch(arch_binary)
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

    if not device_arch:
        error("Device architecture not supported")
        sys_exit()

    device_have_64bit_arch = device_arch in ("arm64", "x86_64")

    print("Creating device tree folders...")
    if device_tree_path.is_dir():
        rmtree(device_tree_path, ignore_errors=True)
    device_tree_path.mkdir(parents=True)
    device_tree_prebuilt_path.mkdir(parents=True)
    device_tree_recovery_root_path.mkdir(parents=True)

    print("Copying kernel...")
    device_kernel_name = ""
    if device_have_kernel:
        if device_arch == "arm":
            device_kernel_name = "zImage"
        elif device_arch == "arm64":
            device_kernel_name = "Image.gz"
        elif device_arch in ("x86", "x86_64"):
            device_kernel_name = "bzImage"
        else:
            device_kernel_name = "zImage"
        if device_arch in ("arm", "arm64") and (
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
    render_template(device_tree_path, "Android.mk.jinja2", device_codename=device_codename)

    print("Creating AndroidProducts.mk...")
    render_template(device_tree_path, "AndroidProducts.mk.jinja2", device_codename=device_codename)

    print("Creating BoardConfig.mk...")
    render_template(device_tree_path, "BoardConfig.mk.jinja2",
                    device_manufacturer=device_manufacturer,
                    device_codename=device_codename,
                    device_arch=device_arch,
                    device_board_name=device_board_name,
                    device_recovery_size=device_recovery_size,
                    device_is_ab=device_is_ab,
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
                    device_platform=device_platform,
                    flash_block_size=str(int(device_pagesize) * 64)
                    )

    print("Creating device.mk...")
    render_template(device_tree_path, "device.mk.jinja2",
                    device_codename=device_codename,
                    device_manufacturer=device_manufacturer,
                    device_platform=device_platform,
                    device_is_ab=device_is_ab)

    print("Creating omni_" + device_codename + ".mk...")
    render_template(device_tree_path, "omni.mk.jinja2", out_file=f"omni_{device_codename}.mk",
                    device_codename=device_codename,
                    device_manufacturer=device_manufacturer,
                    device_brand=device_brand,
                    device_model=device_model,
                    device_have_64bit_arch=device_have_64bit_arch
                    )

    print("Creating vendorsetup.sh...")
    render_template(device_tree_path, "vendorsetup.sh.jinja2", device_codename=device_codename)

    dt_repo = Repo.init(device_tree_path)
    with dt_repo.config_writer() as git_config:
        git_config.set_value('user', 'email', 'barezzisebastiano@gmail.com')
        git_config.set_value('user', 'name', 'Sebastiano Barezzi')
    dt_repo.index.add(["*"])
    commit_message = render_template(None, "commit_message.jinja2", to_file=False,
                                     device_codename=device_codename,
                                     device_arch=device_arch,
                                     device_manufacturer=device_manufacturer,
                                     device_brand=device_brand,
                                     device_model=device_model,
                                     last_commit=last_commit)
    dt_repo.index.commit(commit_message)
    print(f"\nDone! You can find the device tree in {str(device_tree_path)}")
