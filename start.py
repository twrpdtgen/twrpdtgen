#!/usr/bin/python

import errno
import git
from git.exc import InvalidGitRepositoryError
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
from sys import argv
from twrpdtgen.misc import append_license, error, get_device_arch, make_twrp_fstab, open_file_and_read, printhelp

version_major = "1"
version_minor = "0"
version_quickfix = "0"
version = version_major + "." + version_minor + "." + version_quickfix

try:
	twrpdtgen_repo = git.Repo(os.getcwd())
except InvalidGitRepositoryError:
	error("Please clone the script with Git instead of downloading it as a zip")
	exit()
last_commit = twrpdtgen_repo.head.object.hexsha
last_commit = last_commit[:7]

print("TWRP device tree generator")
print("Python edition")
print("Version " + version)
print("")

try:
	recovery_image = argv[1]
except IndexError:
	error("Recovery image not provided")
	printhelp()
	exit()

if not os.path.isfile(recovery_image):
	error("Recovery image doesn't exist")
	printhelp()
	exit()

device_codename = input("Enter the device codename: ")
device_full_name = input("Enter the device full name: ")
device_manufacturer = input("Enter the device manufacturer: ")
device_release_year = input("Enter the device release year: ")
device_is_ab = input("Is the device A/B? (y/N): ")

if device_codename == "":
	error("Device codename can't be empty")
	exit()
if device_full_name == "":
	error("Device full name can't be empty")
	exit()
if device_manufacturer == "":
	error("Device manufacturer can't be empty")
	exit()
if device_release_year == "":
	error("Device release year can't be empty")
	exit()

device_manufacturer = device_manufacturer.lower()

if device_is_ab == "y" or device_is_ab == "Y":
	device_is_ab = True
elif device_is_ab == "" or device_is_ab == "n" or device_is_ab == "N":
	device_is_ab = False

print("")

# Define paths
current_path = Path(os.getcwd())
aik_path = current_path / "extract"
working_path = current_path / "working"
aik_images_path = aik_path / "split_img"
aik_images_path_base = str(aik_images_path / (device_codename + ".img-"))
aik_ramdisk_path = aik_path / "ramdisk"
device_tree_path = working_path / device_manufacturer / device_codename
device_tree_prebuilt_path = device_tree_path / "prebuilt"
device_tree_recovery_root_path = device_tree_path / "recovery" / "root"
device_tree_files = ["Android.mk", "AndroidProducts.mk", "BoardConfig.mk", "device.mk", "omni_" + device_codename + ".mk", "vendorsetup.sh"]

print("Cloning AIK...")
def handleRemoveReadonly(func, path, exc):
	os.chmod(path, stat.S_IWRITE)
	func(path)
if os.path.isdir(aik_path):
	shutil.rmtree(aik_path, ignore_errors=False, onerror=handleRemoveReadonly)
if platform.system() == "Linux":
	git.Repo.clone_from("https://github.com/SebaUbuntu/AIK-Linux-mirror", aik_path)
elif platform.system() == "Windows":
	git.Repo.clone_from("https://github.com/SebaUbuntu/AIK-Windows-mirror", aik_path)

print("Creating device tree folders...")
if os.path.isdir(device_tree_path):
	shutil.rmtree(device_tree_path, ignore_errors=True)
os.makedirs(device_tree_path)
os.makedirs(device_tree_prebuilt_path)
os.makedirs(device_tree_recovery_root_path)

print("Appending license headers to device tree files...")
for file in device_tree_files:
	append_license(device_tree_path / file, device_release_year, "#")

print("Extracting recovery image...")
new_recovery_image = aik_path / (device_codename + ".img")
shutil.copyfile(recovery_image, new_recovery_image)
if platform.system() == "Linux":
	aik_process = subprocess.Popen([aik_path / "unpackimg.sh", "--nosudo", new_recovery_image],
				stdout=subprocess.PIPE, 
				stderr=subprocess.PIPE,
				universal_newlines=True)
	aik_stdout, aik_stderr = aik_process.communicate()
elif platform.system() == "Windows":
	subprocess.call([aik_path / "unpackimg.bat", new_recovery_image])

print("Getting device infos...")
if os.path.isfile(aik_ramdisk_path / "sbin" / "recovery"):
	arch_binary = aik_ramdisk_path / "sbin" / "recovery"
elif os.path.isfile(aik_ramdisk_path / "sbin" / "setlockstate"):
	arch_binary = aik_ramdisk_path / "sbin" / "setlockstate"
elif os.path.isfile(aik_ramdisk_path / "init"):
	arch_binary = aik_ramdisk_path / "init"
else:
	error("No expected binary has been found")
	exit()

device_arch = get_device_arch(arch_binary)
device_have_kernel = os.path.isfile(aik_images_path / (device_codename + ".img" + "-" + "zImage"))
device_have_dt_image = os.path.isfile(aik_images_path / (device_codename + ".img" + "-" + "dt"))
device_have_dtb_image = os.path.isfile(aik_images_path / (device_codename + ".img" + "-" + "dtb"))
device_have_dtbo_image = os.path.isfile(aik_images_path / (device_codename + ".img" + "-" + "dtbo"))
device_base_address = open_file_and_read(aik_images_path_base + "base")
device_board_name = open_file_and_read(aik_images_path_base + "board")
device_cmdline = open_file_and_read(aik_images_path_base + "cmdline")
device_hash_type = open_file_and_read(aik_images_path_base + "hashtype")
device_header_version = open_file_and_read(aik_images_path_base + "header_version")
device_image_type = open_file_and_read(aik_images_path_base + "imgtype")
device_kernel_offset = open_file_and_read(aik_images_path_base + "kernel_offset")
device_recovery_size = open_file_and_read(aik_images_path_base + "origsize")
device_recovery_sp = open_file_and_read(aik_images_path_base + "os_patch_level")
device_recovery_version = open_file_and_read(aik_images_path_base + "os_version")
device_pagesize = open_file_and_read(aik_images_path_base + "pagesize")
device_ramdisk_compression = open_file_and_read(aik_images_path_base + "ramdiskcomp")
device_ramdisk_offset = open_file_and_read(aik_images_path_base + "ramdisk_offset")
device_second_offset = open_file_and_read(aik_images_path_base + "second_offset")
device_tags_offset = open_file_and_read(aik_images_path_base + "tags_offset")

if device_arch == False:
	error("Device architecture not supported")
	exit()

device_have_64bit_arch = (device_arch == "arm64" or device_arch == "x86_64")

if device_have_kernel:
	if device_arch == "arm":
		device_kernel_name = "zImage"
	elif device_arch == "arm64":
		device_kernel_name = "Image.gz"
	elif device_arch == "x86" or device_arch == "x86_64":
		device_kernel_name = "bzImage"
	else:
		device_kernel_name = "zImage"
	if (device_arch == "arm" or device_arch == "arm64") and (not device_have_dt_image and not device_have_dtb_image):
		device_kernel_name += "-dtb"
	shutil.copyfile(aik_images_path / (device_codename + ".img" + "-" + "zImage"), device_tree_prebuilt_path / device_kernel_name)
if device_have_dt_image:
	shutil.copyfile(aik_images_path / (device_codename + ".img" + "-" + "dt"), device_tree_prebuilt_path / "dt.img")
if device_have_dtb_image:
	shutil.copyfile(aik_images_path / (device_codename + ".img" + "-" + "dtb"), device_tree_prebuilt_path / "dtb.img")
if device_have_dtbo_image:
	shutil.copyfile(aik_images_path / (device_codename + ".img" + "-" + "dtbo"), device_tree_prebuilt_path / "dtbo.img")

if os.path.isfile(aik_ramdisk_path / "etc" / "twrp.fstab"):
	print("Found a TWRP fstab, copying it...")
	shutil.copyfile(aik_ramdisk_path / "etc" / "twrp.fstab", device_tree_path / "recovery.fstab")
else:
	print("Generating fstab...")
	make_twrp_fstab(aik_ramdisk_path / "etc" / "recovery.fstab", device_tree_path / "recovery.fstab")

for file in os.listdir(aik_ramdisk_path):
	if file.endswith(".rc") and file != "init.rc":
		if file == "ueventd.rc":
			shutil.copyfile(aik_ramdisk_path / file, device_tree_recovery_root_path / ("ueventd." + device_codename + ".rc"))
		else:
			shutil.copyfile(aik_ramdisk_path / file, device_tree_recovery_root_path / file)

print("Creating Android.mk...")
with open(device_tree_path / "Android.mk", "a") as file:
	file.write("LOCAL_PATH := $(call my-dir)" + "\n")
	file.write("\n")
	file.write("ifeq ($(TARGET_DEVICE)," + device_codename + ")" + "\n")
	file.write("include $(call all-subdir-makefiles,$(LOCAL_PATH))" + "\n")
	file.write("endif" + "\n")
	file.close()

print("Creating AndroidProducts.mk...")
with open(device_tree_path / "AndroidProducts.mk", "a") as file:
	file.write("PRODUCT_MAKEFILES := \\" + "\n")
	file.write("    $(LOCAL_DIR)/omni_" + device_codename + ".mk" + "\n")
	file.close()

print("Creating BoardConfig.mk...")
with open(device_tree_path / "BoardConfig.mk", "a") as file:
	file.write("DEVICE_PATH := device" + "/" + device_manufacturer + "/" + device_codename + "\n")
	file.write("\n")
	file.write("# For building with minimal manifest" + "\n")
	file.write("ALLOW_MISSING_DEPENDENCIES := true" + "\n")
	file.write("\n")
	file.write("# Architecture" + "\n")
	if device_arch == "arm64":
		file.write("TARGET_ARCH := arm64" + "\n")
		file.write("TARGET_ARCH_VARIANT := armv8-a" + "\n")
		file.write("TARGET_CPU_ABI := arm64-v8a" + "\n")
		file.write("TARGET_CPU_ABI2 := " + "\n")
		file.write("TARGET_CPU_VARIANT := generic" + "\n")
		file.write("\n")
		file.write("TARGET_2ND_ARCH := arm" + "\n")
		file.write("TARGET_2ND_ARCH_VARIANT := armv7-a-neon" + "\n")
		file.write("TARGET_2ND_CPU_ABI := armeabi-v7a" + "\n")
		file.write("TARGET_2ND_CPU_ABI2 := armeabi" + "\n")
		file.write("TARGET_2ND_CPU_VARIANT := generic" + "\n")
		file.write("TARGET_BOARD_SUFFIX := _64" + "\n")
		file.write("TARGET_USES_64_BIT_BINDER := true" + "\n")
	elif device_arch == "arm":
		file.write("TARGET_ARCH := arm" + "\n")
		file.write("TARGET_ARCH_VARIANT := armv7-a-neon" + "\n")
		file.write("TARGET_CPU_ABI := armeabi-v7a" + "\n")
		file.write("TARGET_CPU_ABI2 := armeabi" + "\n")
		file.write("TARGET_CPU_VARIANT := generic" + "\n")
	elif device_arch == "x86":
		file.write("TARGET_ARCH := x86" + "\n")
		file.write("TARGET_ARCH_VARIANT := generic" + "\n")
		file.write("TARGET_CPU_ABI := x86" + "\n")
		file.write("TARGET_CPU_ABI2 := armeabi-v7a" + "\n")
		file.write("TARGET_CPU_ABI_LIST := x86,armeabi-v7a,armeabi" + "\n")
		file.write("TARGET_CPU_ABI_LIST_32_BIT := x86,armeabi-v7a,armeabi" + "\n")
		file.write("TARGET_CPU_VARIANT := generic" + "\n")
	elif device_arch == "x86_64":
		file.write("TARGET_ARCH := x86_64" + "\n")
		file.write("TARGET_ARCH_VARIANT := x86_64" + "\n")
		file.write("TARGET_CPU_ABI := x86_64" + "\n")
		file.write("TARGET_CPU_ABI2 := " + "\n")
		file.write("TARGET_CPU_VARIANT := generic" + "\n")
		file.write("\n")
		file.write("TARGET_2ND_ARCH := x86" + "\n")
		file.write("TARGET_2ND_ARCH_VARIANT := x86" + "\n")
		file.write("TARGET_2ND_CPU_ABI := x86" + "\n")
		file.write("TARGET_2ND_CPU_VARIANT := generic" + "\n")
		file.write("TARGET_BOARD_SUFFIX := _64" + "\n")
		file.write("TARGET_USES_64_BIT_BINDER := true" + "\n")
	file.write("\n")
	file.write("# Assert" + "\n")
	file.write("TARGET_OTA_ASSERT_DEVICE := " + device_codename + "\n")
	file.write("\n")
	if device_board_name != "":
		file.write("# Bootloader" + "\n")
		file.write("TARGET_BOOTLOADER_BOARD_NAME := " + device_board_name + "\n")
		file.write("\n")
	file.write("# File systems" + "\n")
	file.write("BOARD_HAS_LARGE_FILESYSTEM := true" + "\n")
	file.write("#BOARD_RECOVERYIMAGE_PARTITION_SIZE := " + device_recovery_size + " # This is the maximum known partition size, but it can be higher, so we just omit it" + "\n")
	file.write("BOARD_SYSTEMIMAGE_PARTITION_TYPE := ext4" + "\n")
	file.write("BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := ext4" + "\n")
	file.write("BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4" + "\n")
	file.write("TARGET_USERIMAGES_USE_EXT4 := true" + "\n")
	file.write("TARGET_USERIMAGES_USE_F2FS := true" + "\n")
	file.write("TARGET_COPY_OUT_VENDOR := vendor" + "\n")
	file.write("\n")
	if device_is_ab:
		file.write("# A/B" + "\n")
		file.write("AB_OTA_UPDATER := true" + "\n")
		file.write("TW_INCLUDE_REPACKTOOLS := true" + "\n")
	file.write("# Kernel" + "\n")
	file.write("BOARD_KERNEL_CMDLINE := " + device_cmdline + "\n")
	if device_have_kernel:
		file.write("TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/" + device_kernel_name + "\n")
	if device_have_dt_image:
		file.write("TARGET_PREBUILT_DT := $(DEVICE_PATH)/prebuilt/dt.img" + "\n")
	if device_have_dtb_image:
		file.write("TARGET_PREBUILT_DTB := $(DEVICE_PATH)/prebuilt/dtb.img" + "\n")
	if device_have_dtbo_image:
		file.write("BOARD_PREBUILT_DTBOIMAGE := $(DEVICE_PATH)/prebuilt/dtbo.img" + "\n")
		file.write("BOARD_INCLUDE_RECOVERY_DTBO := true" + "\n")
	if device_header_version != "0":
		file.write("BOARD_BOOTIMG_HEADER_VERSION := " + device_header_version + "\n")
	file.write("BOARD_KERNEL_BASE := " + device_base_address + "\n")
	file.write("BOARD_KERNEL_PAGESIZE := " + device_pagesize + "\n")
	file.write("BOARD_RAMDISK_OFFSET := " + device_ramdisk_offset + "\n")
	file.write("BOARD_KERNEL_TAGS_OFFSET := " + device_tags_offset + "\n")
	file.write("BOARD_FLASH_BLOCK_SIZE := " + str(int(device_pagesize) * 64) + " # (BOARD_KERNEL_PAGESIZE * 64)" + "\n")
	file.write("BOARD_MKBOOTIMG_ARGS += --ramdisk_offset $(BOARD_RAMDISK_OFFSET)" + "\n")
	file.write("BOARD_MKBOOTIMG_ARGS += --tags_offset $(BOARD_KERNEL_TAGS_OFFSET)" + "\n")
	if device_have_dt_image:
		file.write("BOARD_MKBOOTIMG_ARGS += --dt $(TARGET_PREBUILT_DT)" + "\n")
	if device_have_dtb_image:
		file.write("BOARD_MKBOOTIMG_ARGS += --dtb $(TARGET_PREBUILT_DTB)" + "\n")
	if device_header_version != "0":
		file.write("BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOTIMG_HEADER_VERSION)" + "\n")
	file.write("TARGET_KERNEL_ARCH := " + device_arch + "\n")
	file.write("TARGET_KERNEL_HEADER_ARCH := " + device_arch + "\n")
	file.write("TARGET_KERNEL_SOURCE := kernel/" + device_manufacturer + "/" + device_codename + "\n")
	file.write("TARGET_KERNEL_CONFIG := " + device_codename + "_defconfig" + "\n")
	file.write("\n")
	if device_ramdisk_compression == "lzma":
		file.write("# Ramdisk compression" + "\n")
		file.write("LZMA_RAMDISK_TARGETS := recovery" + "\n")
		file.write("\n")
	file.write("# Platform" + "\n")
	file.write("#TARGET_BOARD_PLATFORM := " + "\n")
	file.write("#TARGET_BOARD_PLATFORM_GPU := " + "\n")
	file.write("\n")
	file.write("# Hack: prevent anti rollback" + "\n")
	file.write("PLATFORM_SECURITY_PATCH := 2099-12-31" + "\n")
	file.write("PLATFORM_VERSION := 16.1.0" + "\n")
	file.write("\n")
	file.write("# TWRP Configuration" + "\n")
	file.write("TW_THEME := portrait_hdpi" + "\n")
	file.write("TW_EXTRA_LANGUAGES := true" + "\n")
	file.write("TW_SCREEN_BLANK_ON_BOOT := true" + "\n")
	file.write('TW_INPUT_BLACKLIST := "hbtp_vm"' + "\n")
	file.write("TW_USE_TOOLBOX := true" + "\n")
	file.close()

print("Creating device.mk...")
with open(device_tree_path / "device.mk", "a") as file:
	file.write("LOCAL_PATH := device" + "/" + device_manufacturer + "/" + device_codename + "\n")
	if device_is_ab:
		file.write("# A/B" + "\n")
		file.write("AB_OTA_PARTITIONS += \\" + "\n")
		file.write("	boot \\" + "\n")
		file.write("	system \\" + "\n")
		file.write("	vendor" + "\n")
		file.write("\n")
		file.write("AB_OTA_POSTINSTALL_CONFIG += \\" + "\n")
		file.write("	RUN_POSTINSTALL_system=true \\" + "\n")
		file.write("	POSTINSTALL_PATH_system=system/bin/otapreopt_script \\" + "\n")
		file.write("	FILESYSTEM_TYPE_system=ext4 \\" + "\n")
		file.write("	POSTINSTALL_OPTIONAL_system=true" + "\n")
		file.write("\n")
		file.write("# Boot control HAL" + "\n")
		file.write("PRODUCT_PACKAGES += \\" + "\n")
		file.write("	android.hardware.boot@1.0-impl \\" + "\n")
		file.write("	android.hardware.boot@1.0-service" + "\n")
		file.write("\n")
		file.write("PRODUCT_PACKAGES += \\" + "\n")
		file.write("	bootctrl.$(TARGET_BOARD_PLATFORM)" + "\n")
		file.write("\n")
		file.write("PRODUCT_STATIC_BOOT_CONTROL_HAL := \\" + "\n")
		file.write("	bootctrl.$(TARGET_BOARD_PLATFORM) \\" + "\n")
		file.write("	libgptutils \\" + "\n")
		file.write("	libz \\" + "\n")
		file.write("	libcutils" + "\n")
		file.write("\n")
		file.write("PRODUCT_PACKAGES += \\" + "\n")
		file.write("	otapreopt_script \\" + "\n")
		file.write("	cppreopts.sh \\" + "\n")
		file.write("	update_engine \\" + "\n")
		file.write("	update_verifier \\" + "\n")
		file.write("	update_engine_sideload" + "\n")
	file.close()

print("Creating omni_" + device_codename + ".mk...")
with open(device_tree_path / ("omni_" + device_codename + ".mk"), "a") as file:
	file.write("# Inherit from those products. Most specific first." + "\n")
	if device_have_64bit_arch:
		file.write("$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)" + "\n")
	file.write("$(call inherit-product-if-exists, $(SRC_TARGET_DIR)/product/embedded.mk)" + "\n")
	file.write("$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)" + "\n")
	file.write("$(call inherit-product, $(SRC_TARGET_DIR)/product/languages_full.mk)" + "\n")
	file.write("\n")
	file.write("# Inherit from " + device_codename + " device" + "\n")
	file.write("$(call inherit-product, device/" + device_manufacturer + "/" + device_codename + "/device.mk)" + "\n")
	file.write("\n")
	file.write("# Inherit some common Omni stuff." + "\n")
	file.write("$(call inherit-product, vendor/omni/config/common.mk)" + "\n")
	file.write("$(call inherit-product, vendor/omni/config/gsm.mk)" + "\n")
	file.write("\n")
	file.write("# Device identifier. This must come after all inclusions" + "\n")
	file.write("PRODUCT_DEVICE := " + device_codename + "\n")
	file.write("PRODUCT_NAME := omni_" + device_codename + "\n")
	file.write("PRODUCT_BRAND := " + device_manufacturer + "\n")
	file.write("PRODUCT_MODEL := " + device_full_name + "\n")
	file.write("PRODUCT_MANUFACTURER := " + device_manufacturer + "\n")
	file.write("PRODUCT_RELEASE_NAME := " + device_full_name + "\n")
	file.close()

print("Creating vendorsetup.sh...")
with open(device_tree_path / "vendorsetup.sh", "a") as file:
	file.write("add_lunch_combo omni_" + device_codename + "-userdebug" + "\n")
	file.write("add_lunch_combo omni_" + device_codename + "-eng" + "\n")
	file.close()

dt_repo = git.Repo.init(device_tree_path)
with dt_repo.config_writer() as git_config:
	git_config.set_value('user', 'email', 'barezzisebastiano@gmail.com')
	git_config.set_value('user', 'name', 'Sebastiano Barezzi')
dt_repo.index.add(["*"])
commit_message = device_codename + ": Initial TWRP device tree" + "\n"
commit_message += "Made with SebaUbuntu's TWRP device tree generator" + "\n"
commit_message += "Arch: " + device_arch + "\n"
commit_message += "Manufacturer: " + device_manufacturer + "\n"
commit_message += "Device full name: " + device_full_name + "\n"
commit_message += "Script version: " + version + "\n"
commit_message += "Last script commit: " + last_commit + "\n"
commit_message += "Signed-off-by: Sebastiano Barezzi <barezzisebastiano@gmail.com>"
dt_repo.index.commit(commit_message)

print("")
print("Done! You can find the device tree in " + str(device_tree_path))
print("Note: You should open BoardConfig.mk and fix TARGET_BOARD_PLATFORM, TARGET_BOARD_PLATFORM_GPU and BOARD_RECOVERYIMAGE_PARTITION_SIZE")
