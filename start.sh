#!/bin/bash
#
# Copyright (C) 2020 The Android Open Source Project
# Copyright (C) 2020 The TWRP Open Source Project
# Copyright (C) 2020 SebaUbuntu's TWRP device tree generator 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

VERSION="1.2"

SCRIPT_PWD=$(pwd)

if [ "$1" = "--cli" ]; then
	USE_GUI=false
fi

# Source additional tools
if [ ! -f ./tools/adb.sh ]; then
	echo "Please fully clone the script"
	exit
fi
source ./tools/adb.sh
source ./tools/files.sh
source ./tools/fstab.sh
source ./tools/graphics.sh
source ./tools/user_interaction.sh

set_colors
clean_screen
logo

LAST_COMMIT=$(git log -1 --format="%h")
if [ ${#LAST_COMMIT} != 7 ]; then
	error "Failed retreiving last git commit
Please use git clone, and don't download repo zip file
If you don't have it, also install git"
	exit
fi

# Ask user for device info because we don't use build.prop
logo
DEVICE_CODENAME=$(get_info "Insert the device codename (eg. whyred)")
if [ -z "$DEVICE_CODENAME" ]; then
	error "Device codename can't be empty"
	exit
fi
clean_screen

logo
DEVICE_MANUFACTURER=$(get_info "Insert the device manufacturer (eg. xiaomi)")
if [ -z "$DEVICE_MANUFACTURER" ]; then
	error "Device manufacturer can't be empty"
	exit
fi
# Manufacturer name must be lowercase
DEVICE_MANUFACTURER=$(echo "$DEVICE_MANUFACTURER" | tr '[:upper:]' '[:lower:]')
clean_screen

logo
DEVICE_YEAR_RELEASE=$(get_info "Insert the device release year (eg. 2018)")
if [ -z "$DEVICE_YEAR_RELEASE" ]; then
	error "Device year release can't be empty"
	exit
fi
clean_screen

logo
DEVICE_FULL_NAME=$(get_info "Insert the device commercial name (eg. Xiaomi Redmi Note 5)")
if [ -z "$DEVICE_FULL_NAME" ]; then
	error "Device commercial name can't be empty"
	exit
fi
clean_screen

logo
DEVICE_IS_AB=$(get_boolean "Is the device A/B?")
if [ -z "$DEVICE_IS_AB" ]; then
	info "Nothing inserted, assuming A-only device"
	sleep 1
elif [ "$DEVICE_IS_AB" != 1 ] && [ "$DEVICE_IS_AB" != 0 ]; then
	error "Wrong input"
	exit
fi
clean_screen

logo
DEVICE_STOCK_RECOVERY_PATH=$(get_file_path "recovery image (or a boot image if the device is A/B)" "*.img")
if [ ! -f "$DEVICE_STOCK_RECOVERY_PATH" ]; then
	error "File not found"
	exit
fi
clean_screen

logo
ADB_CHOICE=$(get_boolean "Do you want to add additional flags via ADB? (Optional)
This can help the script making a better device tree by taking precise data
But you need to have the device on hands and adb command needs to be present")
if [ -z "$ADB_CHOICE" ]; then
	info "Nothing inserted, assuming ADB won't be used"
	sleep 1
elif [ "$ADB_CHOICE" != 1 ] && [ "$ADB_CHOICE" != 0 ]; then
	error "Wrong input"
	exit
fi
clean_screen

# Start generation
logo
if [ -f "$SCRIPT_PWD/$DEVICE_CODENAME.log" ]; then
	rm -f "$SCRIPT_PWD/$DEVICE_CODENAME.log"
fi
loginfo "
------------------------------------------------------------------------
SebaUbuntu's TWRP device tree generator
Version=$VERSION
Device name=$DEVICE_FULL_NAME
Device codename=$DEVICE_CODENAME
Date and time=$(date)
OS=$(uname)
------------------------------------------------------------------------

Starting device tree generation
"

if [ "$ADB_CHOICE" = "1" ]; then
	adb_check_device
	if [ $? = 0 ]; then
		printf "${blue}Device connected, taking values, do not disconnect the device..."
		DEVICE_SOC_MANUFACTURER=$(adb_get_prop ro.hardware)
		DEVICE_CPU_VARIANT=$(adb_get_prop ro.bionic.cpu_variant)
		DEVICE_2ND_CPU_VARIANT=$(adb_get_prop ro.bionic.cpu_variant)
		echo " done${reset}"
	else
		error "Device not connected or ADB is not installed"
		logerror "Device not connected or ADB is not installed"
	fi
else
	loginfo "ADB will be skipped"
fi

if [ "$DEVICE_CPU_VARIANT" = "" ]; then
	loginfo "Value not found with ADB or ADB has not been used, using generic values for 1st CPU variant"
	DEVICE_CPU_VARIANT=generic
fi
if [ "$DEVICE_2ND_CPU_VARIANT" = "" ]; then
	loginfo "Value not found with ADB or ADB has not been used, using generic values for 2nd CPU variant"
	DEVICE_2ND_CPU_VARIANT=generic
fi
if [ "$DEVICE_SOC_MANUFACTURER" != "" ]; then
	loginfo "Device SoC manufacturer is $DEVICE_SOC_MANUFACTURER"
fi

# Path declarations
SPLITIMG_DIR=extract/split_img
RAMDISK_DIR=extract/ramdisk
DEVICE_TREE_PATH="$DEVICE_MANUFACTURER/$DEVICE_CODENAME"

# Start cleanly
rm -rf "$DEVICE_TREE_PATH"
mkdir -p "$DEVICE_TREE_PATH/prebuilt"
mkdir -p "$DEVICE_TREE_PATH/recovery/root"

# Obtain stock recovery.img size
cp "$DEVICE_STOCK_RECOVERY_PATH" "extract/$DEVICE_CODENAME.img"
logstep "Obtaining stock recovery image info..."
IMAGE_FILESIZE=$(du -b "extract/$DEVICE_CODENAME.img" | cut -f1)
cd extract

# Obtain recovery.img format info
./unpackimg.sh --nosudo "$DEVICE_CODENAME.img" > /dev/null 2>&1
cd ..
KERNEL_BOOTLOADER_NAME=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-board")
KERNEL_CMDLINE=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-cmdline")
KERNEL_PAGESIZE=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-pagesize")
KERNEL_BASEADDRESS=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-base")
KERNEL_OFFSET=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-kerneloff")
RAMDISK_OFFSET=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-ramdiskoff")
KERNEL_SECOND_OFFSET=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-secondoff")
KERNEL_TAGS_OFFSET=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-tagsoff")
RAMDISK_COMPRESSION_TYPE=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-ramdiskcomp")
KERNEL_HEADER_VERSION=$(cat "$SPLITIMG_DIR/$DEVICE_CODENAME.img-headerversion")

logdone

# See what arch is by analizing init executable
BINARY=$(file "$RAMDISK_DIR/init")

# // Android 10 change: now init binary is a symlink to /system/etc/init, check for other binary files
if [ "$(echo "$BINARY" | grep -o "symbolic")" = "symbolic" ]; then
	loginfo "Init binary not found, using a random binary"
	for i in $(ls "$RAMDISK_DIR/sbin"); do
		BINARY=$(file "$RAMDISK_DIR/sbin/$i")
		if [ "$(echo "$BINARY" | grep -o "symbolic")" != "symbolic" ]; then
			BINARY_FOUND=true
			break
		fi
		[ "$BINARY_FOUND" ] && break
	done
	if [ "$BINARY_FOUND" != true ]; then
		for i in $(ls "$RAMDISK_DIR/system/lib64"); do
			BINARY=$(file "$RAMDISK_DIR/system/lib64/$i")
			if [ "$(echo "$BINARY" | grep -o "symbolic")" != "symbolic" ]; then
				BINARY_FOUND=true
				break
			fi
			[ "$BINARY_FOUND" ] && break
		done
	fi
	if [ "$BINARY_FOUND" != true ]; then
		for i in $(ls "$RAMDISK_DIR/vendor/lib64"); do
			BINARY=$(file "$RAMDISK_DIR/vendor/lib64/$i")
			if [ "$(echo "$BINARY" | grep -o "symbolic")" != "symbolic" ]; then
				BINARY_FOUND=true
				break
			fi
			[ "$BINARY_FOUND" ] && break
		done
	fi
	if [ "$BINARY_FOUND" != true ]; then
		for i in $(ls "$RAMDISK_DIR/system/lib"); do
			BINARY=$(file "$RAMDISK_DIR/system/lib/$i")
			if [ "$(echo "$BINARY" | grep -o "symbolic")" != "symbolic" ]; then
				BINARY_FOUND=true
				break
			fi
			[ "$BINARY_FOUND" ] && break
		done
	fi
	if [ "$BINARY_FOUND" != true ]; then
		for i in $(ls "$RAMDISK_DIR/vendor/lib"); do
			BINARY=$(file "$RAMDISK_DIR/vendor/lib/$i")
			if [ "$(echo "$BINARY" | grep -o "symbolic")" != "symbolic" ]; then
				BINARY_FOUND=true
				break
			fi
			[ "$BINARY_FOUND" ] && break
		done
	fi
	if [ "$BINARY_FOUND" != true ]; then
		error "Script can't find a binary file, aborting"
		logerror "Script can't find a binary file, aborting"
		exit
	fi
fi

if echo "$BINARY" | grep -q ARM; then
	if echo "$BINARY" | grep -q aarch64; then
		DEVICE_ARCH=arm64
		DEVICE_IS_64BIT=true
	else
		DEVICE_ARCH=arm
		DEVICE_IS_64BIT=false
	fi
elif echo "$BINARY" | grep -q x86; then	
	if echo "$BINARY" | grep -q x86-64; then
		DEVICE_ARCH=x86_64
		DEVICE_IS_64BIT=true
	else
		DEVICE_ARCH=x86
		DEVICE_IS_64BIT=false
	fi
else
	# Nothing matches, were you trying to make TWRP for Symbian OS devices, Playstation 2 or PowerPC-based Macintosh?
	error "Arch not supported"
	logerror "Arch not supported"
	exit
fi

if [ $DEVICE_ARCH = x86_64 ]; then
	# idk how you can have a x86_64 Android based device, unless it's Android-x86 project
	error "x86_64 arch is not supported for now!"
	logerror "x86_64 arch is not supported for now!"
	exit
fi

loginfo "Device is $DEVICE_ARCH"

# Check if device tree blobs are not appended to kernel and copy kernel
if [ -f "$SPLITIMG_DIR/$DEVICE_CODENAME.img-dt" ]; then
	loginfo "DTB are not appended to kernel"
	logstep "Copying kernel..."
	cp "$SPLITIMG_DIR/$DEVICE_CODENAME.img-zImage" "$DEVICE_TREE_PATH/prebuilt/zImage"
	logdone
	logstep "Copying DTB..."
	cp "$SPLITIMG_DIR/$DEVICE_CODENAME.img-dt" "$DEVICE_TREE_PATH/prebuilt/dt.img"
	logdone
else
	loginfo "DTB are appended to kernel"
	logstep "Copying kernel..."
	cp "$SPLITIMG_DIR/$DEVICE_CODENAME.img-zImage" "$DEVICE_TREE_PATH/prebuilt/zImage-dtb"
	logdone
fi

# Check if dtbo image is present
if [ -f "$SPLITIMG_DIR/$DEVICE_CODENAME.img-recoverydtbo" ]; then
	loginfo "DTBO image exists"
	logstep "Copying DTBO..."
	cp "$SPLITIMG_DIR/$DEVICE_CODENAME.img-recoverydtbo" "$DEVICE_TREE_PATH/prebuilt/dtbo.img"
	logdone
fi

# Check if a fstab is present
if [ -f "$RAMDISK_DIR/etc/twrp.fstab" ]; then
	logstep "A TWRP fstab has been found, copying it..."
	cp "$RAMDISK_DIR/etc/twrp.fstab" "$DEVICE_TREE_PATH/recovery.fstab"
	# Do a quick check if vendor partition is present
	if [ $(grep vendor "$DEVICE_TREE_PATH/recovery.fstab" > /dev/null; echo $?) = 0 ]; then
		DEVICE_HAS_VENDOR_PARTITION=true
	fi
	logdone
elif [ -f "$RAMDISK_DIR/etc/recovery.fstab" ]; then
	logstep "Extracting fstab..."
	cp "$RAMDISK_DIR/etc/recovery.fstab" "$DEVICE_TREE_PATH/fstab.temp"
	logdone
elif [ -f "$RAMDISK_DIR/system/etc/recovery.fstab" ]; then
	logstep "Extracting fstab..."
	cp "$RAMDISK_DIR/system/etc/recovery.fstab" "$DEVICE_TREE_PATH/fstab.temp"
	logdone
else
	error "The script haven't found any fstab, so you will need to make your own fstab based on what partitions you have"
	logerror "The script haven't found any fstab"
fi

# Check if recovery.wipe is there
if [ "$DEVICE_IS_AB" ]; then
	logstep "Copying A/B stuff..."
	if [ -f "$RAMDISK_DIR/etc/recovery.wipe" ]; then
		cp "$RAMDISK_DIR/etc/recovery.wipe" "$DEVICE_TREE_PATH/recovery.wipe"
	fi
	logdone
fi

# Extract init.rc files
logstep "Extracting init.rc files..."
for i in $(ls $RAMDISK_DIR | grep ".rc"); do
	if [ "$i" != init.rc ]; then
		cp "$RAMDISK_DIR/$i" "$DEVICE_TREE_PATH/recovery/root"
	fi
done
logdone

# Copying vendor from ramdisk
if [ -d "$RAMDISK_DIR/vendor" ]; then
	loginfo "Vendor folder available"
	logstep "Copying vendor folder..."
	cp -r "$RAMDISK_DIR/vendor" "$DEVICE_TREE_PATH/recovery/root/vendor"
	logdone
fi

# Cleanup
rm "extract/$DEVICE_CODENAME.img"
rm -rf $SPLITIMG_DIR
rm -rf $RAMDISK_DIR

cd "$DEVICE_TREE_PATH"

# License - please keep it as is, thanks
logstep "Adding license headers..."
CURRENT_YEAR="$(date +%Y)"
for file in Android.mk AndroidProducts.mk BoardConfig.mk omni_$DEVICE_CODENAME.mk vendorsetup.sh; do
	license_headers "$file"
done
logdone

# Generate custom fstab if it's not ready
if [ -f fstab.temp ]; then
	logstep "Generating fstab..."
	generate_fstab fstab.temp
	rm fstab.temp
	logdone
fi

# Check for system-as-root setup
if [ "$(cat recovery.fstab | grep -w "system_root")" != "" ]; then
	loginfo "Device is system-as-root"
	DEVICE_IS_SAR=1
else
	loginfo "Device is not system-as-root"
	DEVICE_IS_SAR=0
fi

# Android.mk
logstep "Generating Android.mk..."
echo "LOCAL_PATH := \$(call my-dir)

ifeq (\$(TARGET_DEVICE),$DEVICE_CODENAME)
include \$(call all-subdir-makefiles,\$(LOCAL_PATH))
endif" >> Android.mk
logdone

# AndroidProducts.mk
logstep "Generating AndroidProducts.mk..."
echo "PRODUCT_MAKEFILES := \\
	\$(LOCAL_DIR)/omni_$DEVICE_CODENAME.mk" >> AndroidProducts.mk
logdone

# BoardConfig.mk
logstep "Generating BoardConfig.mk..."
echo "DEVICE_PATH := device/$DEVICE_TREE_PATH

# For building with minimal manifest
ALLOW_MISSING_DEPENDENCIES := true
" >> BoardConfig.mk
# Use arch values based on what has been found in init binary
if [ $DEVICE_ARCH = arm64 ]; then
	echo "# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := $DEVICE_CPU_VARIANT

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv7-a-neon
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := $DEVICE_2ND_CPU_VARIANT
TARGET_BOARD_SUFFIX := _64
TARGET_USES_64_BIT_BINDER := true
" >> BoardConfig.mk
elif [ $DEVICE_ARCH = arm ]; then
	echo "# Architecture
TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_CPU_VARIANT := $DEVICE_CPU_VARIANT
" >> BoardConfig.mk
elif [ $DEVICE_ARCH = x86 ]; then # NOTE! x86 can't be tested by me, if you have a x86 device and you want to test this, feel free to report me results
	echo "# Architecture
TARGET_ARCH := x86
TARGET_ARCH_VARIANT := generic
TARGET_CPU_ABI := x86
TARGET_CPU_ABI2 := armeabi-v7a
TARGET_CPU_ABI_LIST := x86,armeabi-v7a,armeabi
TARGET_CPU_ABI_LIST_32_BIT := x86,armeabi-v7a,armeabi
TARGET_CPU_VARIANT := $DEVICE_CPU_VARIANT
" >> BoardConfig.mk
fi
# Some stock recovery.img doesn't have board name attached, so just ignore it
if [ "$BOOTLOADERNAME" != "" ]; then
	echo "# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := $KERNEL_BOOTLOADER_NAME
" >> BoardConfig.mk
fi

echo "# Kernel
BOARD_KERNEL_CMDLINE := $KERNEL_CMDLINE" >> BoardConfig.mk
if [ "$DEVICE_IS_AB" = 1 ]; then
	echo "BOARD_KERNEL_CMDLINE += skip_override androidboot.fastboot=1" >> BoardConfig.mk
fi
echo "BOARD_KERNEL_BASE := 0x$KERNEL_BASEADDRESS
BOARD_KERNEL_PAGESIZE := $KERNEL_PAGESIZE
BOARD_KERNEL_OFFSET := 0x$KERNEL_OFFSET
BOARD_RAMDISK_OFFSET := 0x$RAMDISK_OFFSET
BOARD_SECOND_OFFSET := 0x$KERNEL_SECOND_OFFSET
BOARD_KERNEL_TAGS_OFFSET := 0x$KERNEL_TAGS_OFFSET
BOARD_FLASH_BLOCK_SIZE := $((KERNEL_PAGESIZE * 64)) # (BOARD_KERNEL_PAGESIZE * 64)" >> BoardConfig.mk

# Add kernel header version only if it's different than 0
# Passing argument 0 to mkbootimg is not allowed
if [ "$KERNEL_HEADER_VERSION" != "0" ]; then
	echo "BOARD_BOOTIMG_HEADER_VERSION := $KERNEL_HEADER_VERSION" >> BoardConfig.mk
fi

# Check for dtb image and add it to BoardConfig.mk
if [ -f prebuilt/dt.img ]; then
	echo "TARGET_PREBUILT_KERNEL := \$(DEVICE_PATH)/prebuilt/zImage
TARGET_PREBUILT_DTB := \$(DEVICE_PATH)/prebuilt/dt.img" >> BoardConfig.mk
else
	echo "TARGET_PREBUILT_KERNEL := \$(DEVICE_PATH)/prebuilt/zImage-dtb" >> BoardConfig.mk
fi

# Check for dtbo image and add it to BoardConfig.mk
if [ -f prebuilt/dtbo.img ]; then
	echo "BOARD_PREBUILT_DTBOIMAGE := \$(DEVICE_PATH)/prebuilt/dtbo.img
BOARD_INCLUDE_RECOVERY_DTBO := true" >> BoardConfig.mk
fi

# Additional mkbootimg arguments
echo "BOARD_MKBOOTIMG_ARGS += --ramdisk_offset \$(BOARD_RAMDISK_OFFSET)
BOARD_MKBOOTIMG_ARGS += --tags_offset \$(BOARD_KERNEL_TAGS_OFFSET)" >> BoardConfig.mk

# Add kernel header version only if it's different than 0
# Passing argument 0 to mkbootimg is not allowed
if [ "$KERNEL_HEADER_VERSION" != "0" ]; then
	echo "BOARD_MKBOOTIMG_ARGS += --header_version \$(BOARD_BOOTIMG_HEADER_VERSION)" >> BoardConfig.mk
fi

if [ -f prebuilt/dt.img ]; then
	echo "BOARD_MKBOOTIMG_ARGS += --dt \$(TARGET_PREBUILT_DTB)" >> BoardConfig.mk
fi

if [ "$DEVICE_MANUFACTURER" = "samsung" ]; then
	echo "BOARD_CUSTOM_BOOTIMG_MK := \$(DEVICE_PATH)/mkbootimg.mk" >> BoardConfig.mk
fi

# Add flags to support kernel building from source
if [ "$DEVICE_ARCH" = arm64 ]; then
	echo "BOARD_KERNEL_IMAGE_NAME := Image.gz-dtb" >> BoardConfig.mk
elif [ "$DEVICE_ARCH" = arm ]; then
	echo "BOARD_KERNEL_IMAGE_NAME := zImage-dtb" >> BoardConfig.mk
elif [ "$DEVICE_ARCH" = x86 ]; then
	echo "BOARD_KERNEL_IMAGE_NAME := bzImage" >> BoardConfig.mk
elif [ "$DEVICE_ARCH" = x86_64 ]; then
	echo "BOARD_KERNEL_IMAGE_NAME := bzImage" >> BoardConfig.mk
fi

echo "TARGET_KERNEL_ARCH := $DEVICE_ARCH
TARGET_KERNEL_HEADER_ARCH := $DEVICE_ARCH
TARGET_KERNEL_SOURCE := kernel/$DEVICE_MANUFACTURER/$DEVICE_CODENAME
TARGET_KERNEL_CONFIG := ${DEVICE_CODENAME}_defconfig
" >> BoardConfig.mk

# Add LZMA compression if kernel suppport it
case $RAMDISK_COMPRESSION_TYPE in
	lzma)
		echo "# LZMA
LZMA_RAMDISK_TARGETS := recovery
" >> BoardConfig.mk
		;;
esac

# Add system-as-root flags if device system-as-root
if [ $DEVICE_IS_SAR = 1 ]; then
	echo "# System as root
BOARD_BUILD_SYSTEM_ROOT_IMAGE := true
BOARD_SUPPRESS_SECURE_ERASE := true
" >> BoardConfig.mk
fi

echo "# Platform
# Fix this
#TARGET_BOARD_PLATFORM := 
#TARGET_BOARD_PLATFORM_GPU := 

# Assert
TARGET_OTA_ASSERT_DEVICE := $DEVICE_CODENAME

# Partitions
#BOARD_RECOVERYIMAGE_PARTITION_SIZE := $IMAGE_FILESIZE # This is the maximum known partition size, but it can be higher, so we just omit it

# File systems
BOARD_HAS_LARGE_FILESYSTEM := true
BOARD_SYSTEMIMAGE_PARTITION_TYPE := ext4
BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true
BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := ext4

# Workaround for error copying vendor files to recovery ramdisk
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_COPY_OUT_VENDOR := vendor

# Hack: prevent anti rollback
PLATFORM_SECURITY_PATCH := 2099-12-31
PLATFORM_VERSION := 16.1.0
" >> BoardConfig.mk

if [ "$DEVICE_IS_AB" = 1 ]; then
	echo "# A/B" >> BoardConfig.mk
	if [ -f recovery.wipe ]; then
		echo "TARGET_RECOVERY_WIPE := \$(DEVICE_PATH)/recovery/root/etc/recovery.wipe" >> BoardConfig.mk
	fi
	echo "AB_OTA_UPDATER := true
TW_INCLUDE_REPACKTOOLS := true" >> BoardConfig.mk
fi

echo "# TWRP Configuration
TW_THEME := portrait_hdpi
TW_EXTRA_LANGUAGES := true
TW_SCREEN_BLANK_ON_BOOT := true
TW_INPUT_BLACKLIST := \"hbtp_vm\"
TW_USE_TOOLBOX := true" >> BoardConfig.mk
logdone

case $RAMDISK_COMPRESSION in
	lzma)
		loginfo "Kernel support lzma compression, using it"
		;;
	lz4)
		loginfo "Kernel support lz4 compression, but I don't know how to enable it .-."
		;;
	xz)
		loginfo "Kernel support xz compression, but I don't know how to enable it .-."
		;;
esac

# omni_device.mk
logstep "Generating omni_$DEVICE_CODENAME.mk..."
echo "# Specify phone tech before including full_phone
\$(call inherit-product, vendor/omni/config/gsm.mk)

# Inherit some common Omni stuff.
\$(call inherit-product, vendor/omni/config/common.mk)
\$(call inherit-product, build/target/product/embedded.mk)

# Inherit Telephony packages
\$(call inherit-product, \$(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit language packages
\$(call inherit-product, \$(SRC_TARGET_DIR)/product/languages_full.mk)
" >> "omni_$DEVICE_CODENAME.mk"

# Inherit 64bit things if device is 64bit
if [ $DEVICE_IS_64BIT = true ]; then
	echo "# Inherit 64bit support
\$(call inherit-product, \$(SRC_TARGET_DIR)/product/core_64_bit.mk)
" >> "omni_$DEVICE_CODENAME.mk"
fi

# Add A/B flags
if [ "$DEVICE_IS_AB" = 1 ]; then
	printf "# A/B
AB_OTA_PARTITIONS += \\
    boot \\
    system" >> "omni_$DEVICE_CODENAME.mk"
	if [ "$DEVICE_HAS_VENDOR_PARTITION" = true ]; then
		echo " \\
    vendor" >> "omni_$DEVICE_CODENAME.mk"
	else
		echo "" >> "omni_$DEVICE_CODENAME.mk"
	fi
	
	echo "
AB_OTA_POSTINSTALL_CONFIG += \\
    RUN_POSTINSTALL_system=true \\
    POSTINSTALL_PATH_system=system/bin/otapreopt_script \\
    FILESYSTEM_TYPE_system=ext4 \\
    POSTINSTALL_OPTIONAL_system=true

# Boot control HAL
PRODUCT_PACKAGES += \\
    android.hardware.boot@1.0-impl \\
    android.hardware.boot@1.0-service

PRODUCT_PACKAGES += \\
    bootctrl.\$(TARGET_BOARD_PLATFORM)
    
PRODUCT_STATIC_BOOT_CONTROL_HAL := \\
    bootctrl.\$(TARGET_BOARD_PLATFORM) \\
    libgptutils \\
    libz \\
    libcutils
    
PRODUCT_PACKAGES += \\
    otapreopt_script \\
    cppreopts.sh \\
    update_engine \\
    update_verifier \\
    update_engine_sideload
" >> "omni_$DEVICE_CODENAME.mk"
fi

echo "# Device identifier. This must come after all inclusions
PRODUCT_DEVICE := $DEVICE_CODENAME
PRODUCT_NAME := omni_$DEVICE_CODENAME
PRODUCT_BRAND := $DEVICE_MANUFACTURER
PRODUCT_MODEL := $DEVICE_FULL_NAME
PRODUCT_MANUFACTURER := $DEVICE_MANUFACTURER
PRODUCT_RELEASE_NAME := $DEVICE_FULL_NAME" >> "omni_$DEVICE_CODENAME.mk"
logdone

# vendorsetup.sh
logstep "Generating vendorsetup.sh..."
echo "add_lunch_combo omni_$DEVICE_CODENAME-userdebug
add_lunch_combo omni_$DEVICE_CODENAME-eng" >> vendorsetup.sh
logdone

# Add system-as-root declaration
if [ $DEVICE_IS_SAR = 1 ]; then
	echo "on fs
	export ANDROID_ROOT /system_root" >> recovery/root/init.recovery.sar.rc
fi

# If this is a Samsung device, add support to SEAndroid status and make an Odin-flashable tar
if [ "$DEVICE_MANUFACTURER" = "samsung" ]; then
	logstep "This is a Samsung device, appending SEANDROIDENFORCE to recovery image with custom mkbootimg..."
	echo "LOCAL_PATH := \$(call my-dir)

\$(INSTALLED_BOOTIMAGE_TARGET): \$(MKBOOTIMG) \$(INTERNAL_BOOTIMAGE_FILES)
	\$(call pretty,\"Target boot image: \$@\")
	\$(hide) \$(MKBOOTIMG) \$(INTERNAL_BOOTIMAGE_ARGS) \$(BOARD_MKBOOTIMG_ARGS) --output \$@
	@echo -e \${CL_CYN}\"Made boot image: \$@\"\${CL_RST}

\$(INSTALLED_RECOVERYIMAGE_TARGET): \$(MKBOOTIMG) \
		\$(recovery_ramdisk) \
		\$(recovery_kernel)
	@echo -e \${CL_CYN}\"----- Making recovery image ------\"\${CL_RST}
	\$(hide) \$(MKBOOTIMG) \$(INTERNAL_RECOVERYIMAGE_ARGS) \$(BOARD_MKBOOTIMG_ARGS) --output \$@
	@echo -e \${CL_CYN}\"Made recovery image: \$@\"\${CL_RST}
	@echo -e \${CL_GRN}\"----- Lying about SEAndroid state to Samsung bootloader ------\"\${CL_RST}
	\$(hide) echo -n \"SEANDROIDENFORCE\" >> \$(INSTALLED_RECOVERYIMAGE_TARGET)
	\$(hide) \$(call assert-max-image-size,\$@,\$(BOARD_RECOVERYIMAGE_PARTITION_SIZE),raw)
" >> mkbootimg.mk
	logdone
fi

# Automatically create a ready-to-push repo
logstep "Creating ready-to-push git repo..."
git init -q
git add -A
# Please don't be an ass and keep authorship
git commit -m "$DEVICE_CODENAME: initial TWRP device tree

Made with SebaUbuntu's TWRP device tree generator
Arch: $DEVICE_ARCH
Manufacturer: $DEVICE_MANUFACTURER
Device full name: $DEVICE_FULL_NAME
Script version: $VERSION
Last script commit: $LAST_COMMIT

Signed-off-by: Sebastiano Barezzi <barezzisebastiano@gmail.com>" --author "Sebastiano Barezzi <barezzisebastiano@gmail.com>" -q
logdone

echo "Device tree successfully made, you can find it in $DEVICE_TREE_PATH

Note: This device tree should already work, but there can be something that prevent booting the recovery, for example a kernel with OEM modifications that doesn't let boot a custom recovery, or that disable touch on recovery
If this is the case, then see if OEM provide kernel sources and build the kernel by yourself
Here below there is the generation log

$(cat $SCRIPT_PWD/$DEVICE_CODENAME.log)" > exit_message.txt
success "exit_message.txt"
rm "exit_message.txt"