#!/bin/sh
#
# Copyright (C) 2020 The Android Open Source Project
# Copyright (C) 2020 The TWRP Open Source Project
# Copyright (C) 2020 SebaUbuntu's TWRP device tree generator 
#
# Licensed under the Apache License, Version 2.0 (the \"License\");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an \"AS IS\" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Clean screen
clear

# Logo function
logo() {
echo "TWRP device tree generator
by SebaUbuntu
"
}

# Ask user for device info because we don't use build.prop
logo
read -p "Insert the device codename (eg. whyred)
> " DEVICE_CODENAME
clear

logo
read -p "Insert the device manufacturer (eg. xiaomi)
> " DEVICE_MANUFACTURER
clear

# Manufacturer name must be lowercase
DEVICE_MANUFACTURER=$(echo "$DEVICE_MANUFACTURER" | tr '[:upper:]' '[:lower:]')

logo
read -p "Insert the device release year (eg. 2018)
> " DEVICE_YEAR_RELEASE
clear

logo
read -p "Insert the device commercial name (eg. Xiaomi Redmi Note 5)
> " DEVICE_FULL_NAME
clear

logo
read -p "Drag and drop or type the full path of stock recovery.img (you can obtain it from stock OTA or with device dump)
> " DEVICE_STOCK_RECOVERY_PATH
clear
DEVICE_STOCK_RECOVERY_PATH=$(echo $DEVICE_STOCK_RECOVERY_PATH | cut -d "'" -f 2)

logo

# Start cleanly
rm -rf $DEVICE_MANUFACTURER/$DEVICE_CODENAME
mkdir -p $DEVICE_MANUFACTURER/$DEVICE_CODENAME/prebuilt
mkdir -p $DEVICE_MANUFACTURER/$DEVICE_CODENAME/recovery/root

# Obtain stock recovery.img size
cp "$DEVICE_STOCK_RECOVERY_PATH" extract/$DEVICE_CODENAME.img
printf "Obtaining stock recovery image info..."
FILESIZE=$(du -b "extract/$DEVICE_CODENAME.img" | cut -f1)
cd extract
chmod 0777 unpackimg.sh

# Obtain recovery.img format info
./unpackimg.sh --nosudo $DEVICE_CODENAME.img > /dev/null
cd ..
EXTRACTION_DIR=extract/split_img
BOOTLOADERNAME=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-board)
CMDLINE=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-cmdline)
PAGESIZE=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-pagesize)
BASEADDRESS=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-base)
KERNELOFFSET=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-kerneloff)
RAMDISKOFFSET=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-ramdiskoff)
SECONDOFFSET=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-secondoff)
TAGSOFFSET=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-tagsoff)
RAMDISKCOMPRESSION=$(cat $EXTRACTION_DIR/$DEVICE_CODENAME.img-ramdiskcomp)

# See what arch is by analizing init executable
INIT=$(file extract/ramdisk/init)
if echo $INIT | grep -q ARM
	then
		if echo $INIT | grep -q aarch64
			then
				DEVICE_ARCH=arm64
				DEVICE_IS_64BIT=true
			else
				DEVICE_ARCH=arm
				DEVICE_IS_64BIT=false
		fi
elif echo $INIT | grep -q x86
	then	
		if echo $INIT | grep -q x86-64
			then
				DEVICE_ARCH=x86_64
				DEVICE_IS_64BIT=true
			else
				DEVICE_ARCH=x86
				DEVICE_IS_64BIT=false
		fi
else
	# Nothing matches, were you trying to make TWRP for Symbian OS devices, Playstation 2 or PowerPC-based Macintosh?
	echo "Arch not supported"
	exit
fi
if [ $DEVICE_ARCH = x86_64 ]
	then
		# idk how you can have a x86_64 Android based device, unless it's Android-x86 project
		echo "NOTE! x86_64 arch is not supported for now!"
		exit
fi
echo " done"

# Check if device tree blobs are not appended to kernel and copy kernel
if [ -f $EXTRACTION_DIR/$DEVICE_CODENAME.img-dt ]
	then
		printf "Copying stock kernel..."
		cp $EXTRACTION_DIR/$DEVICE_CODENAME.img-zImage $DEVICE_MANUFACTURER/$DEVICE_CODENAME/prebuilt/zImage
		echo " done"
		printf "DTB are not appended to kernel, copying..."
		cp $EXTRACTION_DIR/$DEVICE_CODENAME.img-dt $DEVICE_MANUFACTURER/$DEVICE_CODENAME/prebuilt/dt.img
		echo " done"
	else
		printf "Copying stock kernel..."
		cp $EXTRACTION_DIR/$DEVICE_CODENAME.img-zImage $DEVICE_MANUFACTURER/$DEVICE_CODENAME/prebuilt/zImage-dtb
		echo " done"
fi

# Check if a fstab is present
if [ -f extract/ramdisk/etc/twrp.fstab ]
	then
		printf "Extracting fstab already made (this is for sure a custom recovery)..."
		cp extract/ramdisk/etc/recovery.fstab $DEVICE_MANUFACTURER/$DEVICE_CODENAME/recovery.fstab
		echo " done"
elif [ -f extract/ramdisk/etc/recovery.fstab ]
	then
		printf "Extracting stock fstab..."
		cp extract/ramdisk/etc/recovery.fstab $DEVICE_MANUFACTURER/$DEVICE_CODENAME/fstab.temp
		echo " done"
	else
		echo "WARNING! The script haven't found any fstab, so you will need to make your own fstab based on what partitions you have"
fi

# Extract init.rc files
printf "Extracting init.rc files..."
for i in $(ls extract/ramdisk | grep ".rc")
	do
		if [ $i != init.rc ]
			then
				cp extract/ramdisk/$i $DEVICE_MANUFACTURER/$DEVICE_CODENAME/recovery/root
		fi
done
echo " done"

# Cleanup
rm extract/$DEVICE_CODENAME.img
rm -rf extract/split_img
rm -rf extract/ramdisk

cd $DEVICE_MANUFACTURER/$DEVICE_CODENAME

# License - please keep it as is, thanks
printf "Adding license headers..."
CURRENT_YEAR=$(date +%Y)
for file in Android.mk AndroidProducts.mk BoardConfig.mk omni_$DEVICE_CODENAME.mk vendorsetup.sh
	do
echo "#
# Copyright (C) $DEVICE_YEAR_RELEASE The Android Open Source Project
# Copyright (C) $DEVICE_YEAR_RELEASE The TWRP Open Source Project
# Copyright (C) $CURRENT_YEAR SebaUbuntu's TWRP device tree generator 
#
# Licensed under the Apache License, Version 2.0 (the \"License\");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an \"AS IS\" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
" >> $file
done
echo " done"

# Generate custom fstab if it's not ready
if [ -f fstab.temp ]
	then
		printf "Generating fstab..."
		# Header
		echo "# Android fstab file.
# The filesystem that contains the filesystem checker binary (typically /system) cannot
# specify MF_CHECK, and must come before any filesystems that do specify MF_CHECK

# Mount point		FS		Device									Flags" > recovery.fstab
		for i in boot recovery cache system system_root vendor data dtbo
			do
				a=$(cat fstab.temp | grep -wi "/$i" | grep "/dev.*" -o | cut -d " " -f 1 | cut -d "	" -f 1)
				# If /dev doesn't exist, try /emmc
				if [ "$a" = "" ]
					then
						a=$(cat fstab.temp | grep -wi "/$i" | grep "/emmc.*" -o | cut -d " " -f 1 | cut -d "	" -f 1)
				fi
				if [ "$a" != "" ]
					then
						case $i in
							cache)
								echo "/cache			ext4	$a" >> recovery.fstab
								;;
							system)
								echo "/system			ext4	$a
/system_image		emmc	$a		flags=backup=1;flashimg=1" >> recovery.fstab
								;;
							system_root)
								echo "/system_root			ext4	$a		flags=display="System"
/system_image		emmc	$a		flags=backup=1;flashimg=1" >> recovery.fstab
								;;
							vendor)
								echo "/vendor			ext4	$a		flags=display="Vendor";backup=1;wipeingui
/vendor_image		emmc	$a		flags=backup=1;flashimg=1" >> recovery.fstab
								;;
							data)
								echo "/data				ext4	$a		flags=encryptable=footer;length=-16384" >> recovery.fstab
								;;
							persist)
								echo "/persist			ext4	$a" >> recovery.fstab
								;;
							odm)
								echo "/odm				ext4	$a" >> recovery.fstab
								;;
							omr)
								echo "/omr				ext4	$a" >> recovery.fstab
								;;
							cust)
								echo "/cust				ext4	$a" >> recovery.fstab
								;;
							*)
								echo "/$i				emmc	$a" >> recovery.fstab
								;;
						esac
				fi
		done
		# Add External SDCard entry
		echo "
# External storage
/sdcard1			vfat	/dev/block/mmcblk1p1 /dev/block/mmcblk1	flags=fsflags=utf8;display="SDcard";storage;wipeingui;removable" >> recovery.fstab
		rm fstab.temp
		echo " done"
fi

# Check for system-as-root setup
if [ "$(cat recovery.fstab | grep -w "system_root")" != "" ]
	then
		printf "Device is system-as-root, adding necessary flags..."
		DEVICE_IS_SAR=1
		echo " done"

	else
		DEVICE_IS_SAR=0
fi

# Android.mk
printf "Generating Android.mk..."
echo "LOCAL_PATH := \$(call my-dir)

ifeq (\$(TARGET_DEVICE),$DEVICE_CODENAME)
include \$(call all-subdir-makefiles,\$(LOCAL_PATH))
endif" >> Android.mk
echo " done"

# AndroidProducts.mk
printf "Generating AndroidProducts.mk..."
echo "PRODUCT_MAKEFILES := \\
	\$(LOCAL_DIR)/omni_$DEVICE_CODENAME.mk" >> AndroidProducts.mk
echo " done"

# BoardConfig.mk
printf "Generating BoardConfig.mk..."
echo "DEVICE_PATH := device/$DEVICE_MANUFACTURER/$DEVICE_CODENAME

# For building with minimal manifest
ALLOW_MISSING_DEPENDENCIES := true
" >> BoardConfig.mk
# Use arch values based on what has been found in init binary
if [ $DEVICE_ARCH = arm64 ]
	then
		echo "# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := generic

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv7-a-neon
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_BOARD_SUFFIX := _64
TARGET_USES_64_BIT_BINDER := true
" >> BoardConfig.mk
	elif [ $DEVICE_ARCH = arm ]
		then
			echo "# Architecture
TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_CPU_VARIANT := generic
" >> BoardConfig.mk
	elif [ $DEVICE_ARCH = x86 ] # NOTE! x86 can't be tested by me, if you have a x86 device and you want to test this, feel free to report me results
		then
			echo "# Architecture
TARGET_ARCH := x86
TARGET_ARCH_VARIANT := generic
TARGET_CPU_ABI := x86
TARGET_CPU_ABI2 := armeabi-v7a
TARGET_CPU_ABI_LIST := x86,armeabi-v7a,armeabi
TARGET_CPU_ABI_LIST_32_BIT := x86,armeabi-v7a,armeabi
TARGET_CPU_VARIANT := generic
" >> BoardConfig.mk
fi
# Some stock recovery.img doesn't have board name attached, so just ignore it
if [ "$BOOTLOADERNAME" != "" ]
	then
		echo "# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := $BOOTLOADERNAME
" >> BoardConfig.mk
fi

echo "# Kernel
BOARD_KERNEL_CMDLINE := $CMDLINE
BOARD_KERNEL_BASE := 0x$BASEADDRESS
BOARD_KERNEL_PAGESIZE := $PAGESIZE
BOARD_KERNEL_OFFSET := 0x$KERNELOFFSET
BOARD_RAMDISK_OFFSET := 0x$RAMDISKOFFSET
BOARD_SECOND_OFFSET := 0x$SECONDOFFSET
BOARD_KERNEL_TAGS_OFFSET := 0x$TAGSOFFSET
BOARD_FLASH_BLOCK_SIZE := $((PAGESIZE * 64)) # (BOARD_KERNEL_PAGESIZE * 64)" >> BoardConfig.mk

# Check for dtb image and add it to BoardConfig.mk
if [ -f prebuilt/dt.img ]
	then
		echo "TARGET_PREBUILT_KERNEL := \$(DEVICE_PATH)/prebuilt/zImage
BOARD_MKBOOTIMG_ARGS := --dt device/$DEVICE_MANUFACTURER/$DEVICE_CODENAME/prebuilt/dt.img" >> BoardConfig.mk
	else
		echo "TARGET_PREBUILT_KERNEL += \$(DEVICE_PATH)/prebuilt/zImage-dtb" >> BoardConfig.mk
fi

if [ "$DEVICE_MANUFACTURER" = "samsung" ]
	then
		echo "BOARD_CUSTOM_BOOTIMG_MK := \$(DEVICE_PATH)/mkbootimg.mk" >> BoardConfig.mk
fi

# Add LZMA compression if kernel suppport it
case $RAMDISKCOMPRESSION in
	lzma)
		echo "
# LZMA
LZMA_RAMDISK_TARGETS := recovery
" >> BoardConfig.mk
		;;
	lz4)
		echo "" >> BoardConfig.mk
		;;
	xz)
		echo "" >> BoardConfig.mk
		;;
	*)
		echo "" >> BoardConfig.mk
		;;
esac

# Add system-as-root flags if device system-as-root
if [ $DEVICE_IS_SAR = 1 ]
	then
		echo "# System as root
BOARD_BUILD_SYSTEM_ROOT_IMAGE := true
BOARD_SUPPRESS_SECURE_ERASE := true
" >> BoardConfig.mk
fi

echo "# Platform
# It's not needed for booting TWRP, but it should be added
#TARGET_BOARD_PLATFORM := 
#TARGET_BOARD_PLATFORM_GPU := 

# Assert
TARGET_OTA_ASSERT_DEVICE := $DEVICE_CODENAME

# Partitions
#BOARD_RECOVERYIMAGE_PARTITION_SIZE := $FILESIZE # This is the maximum known partition size, but it can be higher, so we just omit it

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

# TWRP Configuration
TW_THEME := portrait_hdpi
TW_EXTRA_LANGUAGES := true
TARGET_RECOVERY_QCOM_RTC_FIX := true
TW_SCREEN_BLANK_ON_BOOT := true
TW_INPUT_BLACKLIST := \"hbtp_vm\"
TW_USE_TOOLBOX := true" >> BoardConfig.mk
echo " done"

case $RAMDISKCOMPRESSION in
	lzma)
		echo "Kernel support lzma compression, using it"
		;;
	lz4)
		echo "Kernel support lz4 compression, but I don't know how to enable it .-."
		;;
	xz)
		echo "Kernel support xz compression, but I don't know how to enable it .-."
		;;
esac

# omni_device.mk
printf "Generating omni_$DEVICE_CODENAME.mk..."
echo "# Specify phone tech before including full_phone
\$(call inherit-product, vendor/omni/config/gsm.mk)

# Inherit some common Omni stuff.
\$(call inherit-product, vendor/omni/config/common.mk)
\$(call inherit-product, build/target/product/embedded.mk)

# Inherit Telephony packages
\$(call inherit-product, \$(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit language packages
\$(call inherit-product, \$(SRC_TARGET_DIR)/product/languages_full.mk)
" >> omni_$DEVICE_CODENAME.mk

# Inherit 64bit things if device is 64bit
if [ $DEVICE_IS_64BIT = true ]
	then
		echo "# Inherit 64bit support
\$(call inherit-product, \$(SRC_TARGET_DIR)/product/core_64_bit.mk)
" >> omni_$DEVICE_CODENAME.mk
fi

echo "# Device identifier. This must come after all inclusions
PRODUCT_DEVICE := $DEVICE_CODENAME
PRODUCT_NAME := omni_$DEVICE_CODENAME
PRODUCT_BRAND := $DEVICE_MANUFACTURER
PRODUCT_MODEL := $DEVICE_FULL_NAME
PRODUCT_MANUFACTURER := $DEVICE_MANUFACTURER
PRODUCT_RELEASE_NAME := $DEVICE_FULL_NAME" >> omni_$DEVICE_CODENAME.mk
echo " done"

# vendorsetup.sh
printf "Generating vendorsetup.sh..."
echo "add_lunch_combo omni_$DEVICE_CODENAME-userdebug
add_lunch_combo omni_$DEVICE_CODENAME-eng" >> vendorsetup.sh
echo " done"

# Add system-as-root declaration
if [ $DEVICE_IS_SAR = 1 ]
	then
		echo "on fs
	export ANDROID_ROOT /system_root" >> recovery/root/init.recovery.sar.rc
fi

# If this is a Samsung device, add support to SEAndroid status and make an Odin-flashable tar
if [ "$DEVICE_MANUFACTURER" = "samsung" ]
	then
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
fi

# Automatically create a ready-to-push repo
if [ $(dpkg-query -W -f='${Status}' git 2>/dev/null | grep -c "ok installed") -eq 0 ]
	then
 		echo "Git is not installed, can't automatically create a repo"
	else
		printf "Creating ready-to-push git repo..."
		git init -q
		git add -A
		# Please don't be an ass and keep authorship
		git commit -m "$DEVICE_CODENAME: initial TWRP device tree

Made with SebaUbuntu's TWRP device tree generator
Arch: $DEVICE_ARCH
Manufacturer: $DEVICE_MANUFACTURER
Device full name: $DEVICE_FULL_NAME" --author "Sebastiano Barezzi <barezzisebastiano@gmail.com>" -q
		echo " done"
fi

echo ""
echo "Device tree successfully made, you can find it in $DEVICE_MANUFACTURER/$DEVICE_CODENAME

NOTE! This device tree should already work, but there can be something that prevent booting the recovery, for example a kernel with OEM modifications that doesn't let boot a custom recovery, or that disable touch on recovery
If this is the case, then see if OEM provide kernel sources and build the kernel by yourself"
