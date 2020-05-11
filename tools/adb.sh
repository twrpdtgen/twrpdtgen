#!/bin/bash
adb_check_device() {
    if [ "$(command -v adb)" != "" ]; then
		echo "ADB is installed"
		echo ""
		echo "Connect your device with USB debugging enabled"
		echo "If asked, on your device grant USB ADB request"
		echo "Waiting for device..."
		ADB_TIMEOUT=0
		while [ $(adb get-state 1>/dev/null 2>&1; echo $?) != "0" ] && [ "ADB_TIMEOUT" != 30 ]; do
			sleep 1
			ADB_TIMEOUT=$(( ADB_TIMEOUT + 1 ))
		done
		if [ "$ADB_COUNTER" = 30 ]; then
			echo "$red Error: Timeout, ADB will not be used $reset"
			sleep 3
			return 1
			break
		else
			echo "$green Device is connected $reset"
			return 0
		fi
	else
		echo "$red Error: ADB is not installed, skipping... $reset"
		return 0
	fi
}

adb_get_prop() {
	adb shell getprop "$1"
}

adb_get_file() {
	adb pull "$1"
}
