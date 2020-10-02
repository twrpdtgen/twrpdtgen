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
from twrpdtgen.misc import append_license, error, get_device_arch, \
    make_twrp_fstab, open_file_and_read, printhelp

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
        printhelp()
        sys_exit()

    if not recovery_image.is_file():
        error("Recovery image doesn't exist")
        printhelp()
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
    device_tree_files = ["Android.mk", "AndroidProducts.mk", "BoardConfig.mk", "device.mk",
                         "omni_" + device_codename + ".mk", "vendorsetup.sh"]

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

    print("Appending license headers to device tree files...")
    for file in device_tree_files:
        append_license(device_tree_path / file, "#")

    if Path(aik_ramdisk_path / "etc" / "twrp.fstab").is_file():
        print("Found a TWRP fstab, copying it...")
        copyfile(aik_ramdisk_path / "etc" / "twrp.fstab", device_tree_path / "recovery.fstab")
    else:
        print("Generating fstab...")
        make_twrp_fstab(aik_ramdisk_path / "etc" / "recovery.fstab",
                        device_tree_path / "recovery.fstab")

    for file in aik_ramdisk_path.iterdir():
        if file.name.endswith(".rc") and file != "init.rc":
            copyfile(aik_ramdisk_path / file, device_tree_recovery_root_path / file)

    print("Creating Android.mk...")
    with open(device_tree_path / "Android.mk", "w") as file:
        file.write(f"LOCAL_PATH := $(call my-dir)\n\n"
                   f"ifeq ($(TARGET_DEVICE), {device_codename})\n"
                   "include $(call all-subdir-makefiles,$(LOCAL_PATH))\n"
                   "endif\n")

    print("Creating AndroidProducts.mk...")
    with open(device_tree_path / "AndroidProducts.mk", "a") as file:
        file.write(f"PRODUCT_MAKEFILES := \\\n"
                   f"    $(LOCAL_DIR)/omni_{device_codename}.mk\n")

    print("Creating BoardConfig.mk...")
    with open(device_tree_path / "BoardConfig.mk", "a") as file:
        file.write(f"DEVICE_PATH := device/{device_manufacturer}/{device_codename}\n\n"
                   "# For building with minimal manifest\n"
                   "ALLOW_MISSING_DEPENDENCIES := true\n\n"
                   "# Architecture\n")
        if device_arch == "arm64":
            file.write("TARGET_ARCH := arm64\n"
                       "TARGET_ARCH_VARIANT := armv8-a\n"
                       "TARGET_CPU_ABI := arm64-v8a\n"
                       "TARGET_CPU_ABI2 := \n"
                       "TARGET_CPU_VARIANT := generic\n\n"
                       "TARGET_2ND_ARCH := arm\n"
                       "TARGET_2ND_ARCH_VARIANT := armv7-a-neon\n"
                       "TARGET_2ND_CPU_ABI := armeabi-v7a\n"
                       "TARGET_2ND_CPU_ABI2 := armeabi\n"
                       "TARGET_2ND_CPU_VARIANT := generic\n"
                       "TARGET_BOARD_SUFFIX := _64\n"
                       "TARGET_USES_64_BIT_BINDER := true\n")
        elif device_arch == "arm":
            file.write("TARGET_ARCH := arm\n"
                       "TARGET_ARCH_VARIANT := armv7-a-neon\n"
                       "TARGET_CPU_ABI := armeabi-v7a\n"
                       "TARGET_CPU_ABI2 := armeabi\n"
                       "TARGET_CPU_VARIANT := generic\n")
        elif device_arch == "x86":
            file.write("TARGET_ARCH := x86\n"
                       "TARGET_ARCH_VARIANT := generic\n"
                       "TARGET_CPU_ABI := x86\n"
                       "TARGET_CPU_ABI2 := armeabi-v7a\n"
                       "TARGET_CPU_ABI_LIST := x86,armeabi-v7a,armeabi\n"
                       "TARGET_CPU_ABI_LIST_32_BIT := x86,armeabi-v7a,armeabi\n"
                       "TARGET_CPU_VARIANT := generic\n")
        elif device_arch == "x86_64":
            file.write("TARGET_ARCH := x86_64\n"
                       "TARGET_ARCH_VARIANT := x86_64\n"
                       "TARGET_CPU_ABI := x86_64\n"
                       "TARGET_CPU_ABI2 := \n"
                       "TARGET_CPU_VARIANT := generic\n\n"
                       "TARGET_2ND_ARCH := x86\n"
                       "TARGET_2ND_ARCH_VARIANT := x86\n"
                       "TARGET_2ND_CPU_ABI := x86\n"
                       "TARGET_2ND_CPU_VARIANT := generic\n"
                       "TARGET_BOARD_SUFFIX := _64\n"
                       "TARGET_USES_64_BIT_BINDER := true\n")
        file.write(f"\n# Assert\n"
                   f"TARGET_OTA_ASSERT_DEVICE := {device_codename}\n\n")
        if device_board_name != "":
            file.write(f"# Bootloader\n"
                       f"TARGET_BOOTLOADER_BOARD_NAME := {device_board_name}\n\n")
        file.write(f"# File systems\n"
                   "BOARD_HAS_LARGE_FILESYSTEM := true\n"
                   f"#BOARD_RECOVERYIMAGE_PARTITION_SIZE := {device_recovery_size} "
                   "# This is the maximum known partition size, "
                   "but it can be higher, so we just omit it\n"
                   "BOARD_SYSTEMIMAGE_PARTITION_TYPE := ext4\n"
                   "BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := ext4\n"
                   "BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4\n"
                   "TARGET_USERIMAGES_USE_EXT4 := true\n"
                   "TARGET_USERIMAGES_USE_F2FS := true\n"
                   "TARGET_COPY_OUT_VENDOR := vendor\n\n")
        if device_is_ab:
            file.write("# A/B\n"
                       "AB_OTA_UPDATER := true\n"
                       "TW_INCLUDE_REPACKTOOLS := true\n")
        file.write(f"# Kernel\n"
                   f"BOARD_KERNEL_CMDLINE := {device_cmdline}\n")
        if device_have_kernel:
            file.write(f"TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/{device_kernel_name}\n")
        if device_have_dt_image:
            file.write("TARGET_PREBUILT_DT := $(DEVICE_PATH)/prebuilt/dt.img\n")
        if device_have_dtb_image:
            file.write("TARGET_PREBUILT_DTB := $(DEVICE_PATH)/prebuilt/dtb.img\n")
        if device_have_dtbo_image:
            file.write("BOARD_PREBUILT_DTBOIMAGE := $(DEVICE_PATH)/prebuilt/dtbo.img\n"
                       "BOARD_INCLUDE_RECOVERY_DTBO := true\n")
        if device_header_version != "0":
            file.write("BOARD_BOOTIMG_HEADER_VERSION := " + device_header_version + "\n")
        file.write(f"BOARD_KERNEL_BASE := {device_base_address}\n"
                   f"BOARD_KERNEL_PAGESIZE := {device_pagesize}\n"
                   f"BOARD_RAMDISK_OFFSET := {device_ramdisk_offset}\n"
                   f"BOARD_KERNEL_TAGS_OFFSET := {device_tags_offset}\n"
                   f"BOARD_FLASH_BLOCK_SIZE := {str(int(device_pagesize) * 64)} "
                   f"# (BOARD_KERNEL_PAGESIZE * 64)\n"
                   f"BOARD_MKBOOTIMG_ARGS += --ramdisk_offset $(BOARD_RAMDISK_OFFSET)\n"
                   "BOARD_MKBOOTIMG_ARGS += --tags_offset $(BOARD_KERNEL_TAGS_OFFSET)\n")
        if device_have_dt_image:
            file.write("BOARD_MKBOOTIMG_ARGS += --dt $(TARGET_PREBUILT_DT)\n")
        if device_have_dtb_image:
            file.write("BOARD_MKBOOTIMG_ARGS += --dtb $(TARGET_PREBUILT_DTB)\n")
        if device_header_version != "0":
            file.write("BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOTIMG_HEADER_VERSION)\n")
        file.write(f"TARGET_KERNEL_ARCH := {device_arch}\n"
                   f"TARGET_KERNEL_HEADER_ARCH := {device_arch}\n"
                   f"TARGET_KERNEL_SOURCE := kernel/{device_manufacturer}/{device_codename}\n"
                   f"TARGET_KERNEL_CONFIG := {device_codename}_defconfig\n\n")
        if device_ramdisk_compression == "lzma":
            file.write("# Ramdisk compression\n"
                       "LZMA_RAMDISK_TARGETS := recovery\n\n")
        file.write(f"# Platform\n"
                   f"TARGET_BOARD_PLATFORM := {device_platform}\n\n"
                   f"# Hack: prevent anti rollback\n"
                   "PLATFORM_SECURITY_PATCH := 2099-12-31\n"
                   "PLATFORM_VERSION := 16.1.0\n\n"
                   "# TWRP Configuration\n"
                   "TW_THEME := portrait_hdpi\n"
                   "TW_EXTRA_LANGUAGES := true\n"
                   "TW_SCREEN_BLANK_ON_BOOT := true\n"
                   "TW_INPUT_BLACKLIST := \"hbtp_vm\"\n"
                   "TW_USE_TOOLBOX := true\n")

    print("Creating device.mk...")
    with open(device_tree_path / "device.mk", "a") as file:
        file.write(f"LOCAL_PATH := device/{device_manufacturer}/{device_codename}\n")
        if device_is_ab:
            file.write(f"# A/B\n"
                       "AB_OTA_PARTITIONS += \\\n"
                       "	boot \\\n"
                       "	system \\\n"
                       "	vendor\n\n"
                       "AB_OTA_POSTINSTALL_CONFIG += \\\n"
                       "	RUN_POSTINSTALL_system=true \\\n"
                       "	POSTINSTALL_PATH_system=system/bin/otapreopt_script \\\n"
                       "	FILESYSTEM_TYPE_system=ext4 \\\n"
                       "	POSTINSTALL_OPTIONAL_system=true\n\n"
                       "# Boot control HAL\n"
                       "PRODUCT_PACKAGES += \\\n"
                       "	android.hardware.boot@1.0-impl \\\n"
                       "	android.hardware.boot@1.0-service\n\n"
                       "PRODUCT_PACKAGES += \\\n"
                       f"	bootctrl.{device_platform}\n\n"
                       "PRODUCT_STATIC_BOOT_CONTROL_HAL := \\\n"
                       f"	bootctrl.{device_platform}\\\n"
                       "	libgptutils \\\n"
                       "	libz \\\n"
                       "	libcutils\n\n"
                       "PRODUCT_PACKAGES += \\\n"
                       "	otapreopt_script \\\n"
                       "	cppreopts.sh \\\n"
                       "	update_engine \\\n"
                       "	update_verifier \\\n"
                       "	update_engine_sideload\n")

    print("Creating omni_" + device_codename + ".mk...")
    with open(device_tree_path / ("omni_" + device_codename + ".mk"), "a") as file:
        file.write("# Inherit from those products. Most specific first.\n")
        if device_have_64bit_arch:
            file.write("$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)\n")
        file.write(f"$(call inherit-product-if-exists, $(SRC_TARGET_DIR)/product/embedded.mk)\n"
                   "$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)\n"
                   "$(call inherit-product, $(SRC_TARGET_DIR)/product/languages_full.mk)\n\n"
                   f"# Inherit from {device_codename} device\n"
                   f"$(call inherit-product, device/"
                   f"{device_manufacturer}/{device_codename}/device.mk)"
                   "\n\n# Inherit some common Omni stuff.\n"
                   "$(call inherit-product, vendor/omni/config/common.mk)\n"
                   "$(call inherit-product, vendor/omni/config/gsm.mk)\n\n"
                   "# Device identifier. This must come after all inclusions\n"
                   f"PRODUCT_DEVICE := {device_codename}\n"
                   f"PRODUCT_NAME := omni_{device_codename}\n"
                   f"PRODUCT_BRAND := {device_brand}\n"
                   f"PRODUCT_MODEL := {device_model}\n"
                   f"PRODUCT_MANUFACTURER := {device_manufacturer}\n"
                   f"PRODUCT_RELEASE_NAME := {device_brand} {device_model}\n")

    print("Creating vendorsetup.sh...")
    with open(device_tree_path / "vendorsetup.sh", "a") as file:
        file.write(f"add_lunch_combo omni_{device_codename}-userdebug\n"
                   f"add_lunch_combo omni_{device_codename}-eng\n")

    dt_repo = Repo.init(device_tree_path)
    with dt_repo.config_writer() as git_config:
        git_config.set_value('user', 'email', 'barezzisebastiano@gmail.com')
        git_config.set_value('user', 'name', 'Sebastiano Barezzi')
    dt_repo.index.add(["*"])
    commit_message = f"{device_codename}: Initial TWRP device tree\n" \
                     "Made with SebaUbuntu's TWRP device tree generator\n" \
                     f"Arch: {device_arch}\n" \
                     f"Manufacturer: {device_manufacturer}\n" \
                     f"Device full name: {device_brand} {device_model}\n" \
                     f"Script version: {version}\n" \
                     f"Last script commit: {last_commit}\n" \
                     "Signed-off-by: Sebastiano Barezzi <barezzisebastiano@gmail.com>"
    dt_repo.index.commit(commit_message)
    print(f"\nDone! You can find the device tree in {str(device_tree_path)}")
