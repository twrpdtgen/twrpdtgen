#!/bin/bash
adb_check_device() {
	if [ "$(command -v adb)" != "" ]; then
		echo "ADB is installed

Connect your device with USB debugging enabled
If asked, on your device grant USB ADB request
Waiting for device..."
		ADB_TIMEOUT=0
		while [ $(adb get-state 1>/dev/null 2>&1; echo $?) != "0" ] && [ "$ADB_TIMEOUT" != 30 ]; do
			sleep 1
			ADB_TIMEOUT=$(( ADB_TIMEOUT + 1 ))
		done
		if [ "$ADB_TIMEOUT" = 30 ]; then
			info "Timeout, ADB will not be used"
			loginfo "Timeout, ADB will not be used"
			sleep 1
			return 1
			break
		else
			info "Device is connected"
			loginfo "Device is connected"
			return 0
		fi
	else
		error "ADB is not installed, skipping..."
		logerror "ADB is not installed, skipping..."
		return 0
	fi
}

adb_get_prop() {
	adb shell getprop "$1"
}

adb_get_file() {
	adb pull "$1"
}
