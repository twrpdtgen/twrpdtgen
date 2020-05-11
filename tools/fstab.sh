generate_fstab() {
    if [ -f "$1" ]; then
		# Header
    	echo "# Android fstab file.
# The filesystem that contains the filesystem checker binary (typically /system) cannot
# specify MF_CHECK, and must come before any filesystems that do specify MF_CHECK

# Mount point		FS		Device									Flags" > recovery.fstab
	    for i in boot recovery cache system system_root vendor data dtbo; do
	    	a=$(cat "$1" | grep -wi "/$i" | grep "/dev.*" -o | cut -d " " -f 1 | cut -d "	" -f 1)
		    # If /dev doesn't exist, try /emmc
	    	if [ "$a" = "" ]; then
		    	a=$(cat "$1" | grep -wi "/$i" | grep "/emmc.*" -o | cut -d " " -f 1 | cut -d "	" -f 1)
	    	fi
	    	if [ "$a" != "" ]; then
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
	    				DEVICE_HAS_VENDOR_PARTITION=true
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
	else
		echo "$red fastab not found!"
		exit
    fi
}
