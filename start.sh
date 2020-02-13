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
read -p "Insert the device manufacturer (eg. Xiaomi)
> " DEVICE_MANUFACTURER
clear

logo
read -p "Insert the device release year (eg. 2018)
> " DEVICE_YEAR_RELEASE
clear

logo
read -p "Insert the device full name (or commercial name) (eg. Xiaomi Redmi Note 5)
> " DEVICE_FULL_NAME
clear

logo
read -p "Drag and drop stock recovery.img or type the full path of the file (you can obtain it from stock OTA or with device dump)
> " DEVICE_STOCK_RECOVERY_PATH
clear
DEVICE_STOCK_RECOVERY_PATH=$(echo $DEVICE_STOCK_RECOVERY_PATH | cut -d "'" -f 2)

logo

# Start cleanly
rm -rf $DEVICE_MANUFACTURER/$DEVICE_CODENAME
mkdir -p $DEVICE_MANUFACTURER/$DEVICE_CODENAME/prebuilt
mkdir -p $DEVICE_MANUFACTURER/$DEVICE_CODENAME/recovery/root

# Start analizing stock recovery.img and extract kernel
printf "Extracting stock kernel and grabbing device info..."
cp $DEVICE_STOCK_RECOVERY_PATH extract/$DEVICE_CODENAME.img
# Obtain stock recovery.img size
FILESIZE=$(du -b "extract/$DEVICE_CODENAME.img" | cut -f1)
cd extract
chmod 0777 split_boot
chmod 0777 boot_info
# Obtain recovery.img format info
./split_boot $DEVICE_CODENAME.img > result.txt
RESULT=$(cat result.txt)
BOOTLOADERNAME=$(echo "$RESULT" | grep "Board name" | sed -e "s/^Board name: //")
CMDLINE=$(./boot_info $DEVICE_CODENAME.img | grep "CMDLINE" | sed -e "s/^CMDLINE: //" | cut -d "'" -f 2)
PAGESIZE=$(./boot_info $DEVICE_CODENAME.img | grep "PAGE SIZE" | sed -e "s/^PAGE SIZE: //")
BASEADDRESS=$(./boot_info $DEVICE_CODENAME.img | grep "BASE ADDRESS" | sed -e "s/^BASE ADDRESS: //")
RAMDISKADDRESS=$(./boot_info $DEVICE_CODENAME.img | grep "RAMDISK ADDRESS" | sed -e "s/^RAMDISK ADDRESS: //")
# See what arch is by analizing init executable
INIT=$(file $DEVICE_CODENAME/ramdisk/init)
if echo $INIT | grep -q ARM
	then
		if echo $INIT | grep -q aarch64
			then
				DEVICE_ARCH=arm64
				DEVICE_IS_64BIT=true
			else
				DEVICE_ARCH=arm
		fi
elif echo $INIT | grep -q x86
	then	
		if echo $INIT | grep -q x86-64
			then
				DEVICE_ARCH=x86_64
				DEVICE_IS_64BIT=true
			else
				DEVICE_ARCH=x86
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

cd ..
cp extract/$DEVICE_CODENAME/$DEVICE_CODENAME.img-kernel $DEVICE_MANUFACTURER/$DEVICE_CODENAME/prebuilt/kernel
if [ -f extract/$DEVICE_CODENAME/ramdisk/etc/recovery.fstab ]
	then
		# Ooooh, you are very lucky, it seems that your OEM did all the work for me, a ready-to-use fstab
		cp extract/$DEVICE_CODENAME/ramdisk/etc/recovery.fstab $DEVICE_MANUFACTURER/$DEVICE_CODENAME
	else
		cp extract/$DEVICE_CODENAME/ramdisk/fstab.qcom $DEVICE_MANUFACTURER/$DEVICE_CODENAME/recovery/root
fi
echo " done"

# Cleanup
rm extract/$DEVICE_CODENAME.img
rm -rf extract/$DEVICE_CODENAME
rm extract/result.txt

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
echo "LOCAL_PATH := device/$DEVICE_MANUFACTURER/$DEVICE_CODENAME

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
if [ !"$BOOTLOADERNAME" = "" ]
	then
		echo "# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := $BOOTLOADERNAME
" >> BoardConfig.mk
fi

echo "# Kernel
BOARD_KERNEL_CMDLINE := $CMDLINE
BOARD_KERNEL_BASE := $BASEADDRESS
BOARD_KERNEL_PAGESIZE := $PAGESIZE
BOARD_RAMDISK_OFFSET := $RAMDISKADDRESS
BOARD_FLASH_BLOCK_SIZE := $((KERNEL_PAGE_SIZE * 64))
TARGET_PREBUILT_KERNEL := device/$DEVICE_MANUFACTURER/$DEVICE_CODENAME/prebuilt/kernel

# Platform
# It's not needed for booting TWRP, but it should be added
#TARGET_BOARD_PLATFORM := sdm660 #Change this
#TARGET_BOARD_PLATFORM_GPU := qcom-adreno509 #Change this

# Assert
TARGET_OTA_ASSERT_DEVICE := $DEVICE_CODENAME

# Partitions
BOARD_RECOVERYIMAGE_PARTITION_SIZE := $FILESIZE

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
