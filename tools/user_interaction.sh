#!/bin/bash
info() {
	if [ "$USE_GUI" = false ]; then
		echo "${blue}Info: ${1}${reset}"
	else
		zenity --info --text "Info: ${1}" --title "TWRP device tree generator" --width 300
	fi
}

success() {
	if [ "$USE_GUI" = false ]; then
		echo "${green}Success: ${1}${reset}"
	else
		zenity --text-info --filename="${1}" --title "TWRP device tree generator" --width=800 --height=600
	fi
}

error() {
	if [ "$USE_GUI" = false ]; then
		echo "${red}Error: ${1}${reset}"
	else
		zenity --error --text "Error: ${1}" --title "TWRP device tree generator" --width 300
	fi
}

get_info() {
	if [ "$USE_GUI" = false ]; then
		temp=""
		read -p "${1}
> " temp
		echo "$temp"
	else
		zenity --entry --text "Info: ${1}" --title "TWRP device tree generator" --width 300
	fi
}

get_boolean() {
	if [ "$USE_GUI" = false ]; then
		temp=""
		read -p "${1} Type 1 to confirm
> " temp
		echo "$temp"
	else
		zenity --question --text "${1}" --title "TWRP device tree generator" --width 300
		local answer=$?
		if [ "$answer" = "1" ]; then
			echo 0
		elif [ "$answer" = "0" ]; then
			echo 1
		else
			echo "$answer"
		fi
	fi
}

get_file_path() {
	if [ "$USE_GUI" = false ]; then
		temp=""
		read -p "Drag and drop or type the full path of ${1}
> " temp
		temp=$(echo "$temp" | cut -d "'" -f 2)
		echo "$temp"
	else
		zenity --file-selection --title "Select a ${1}" --file-filter="${2}"
	fi
}