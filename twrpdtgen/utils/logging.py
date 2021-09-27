#
# Copyright (C) 2021 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from logging import basicConfig, INFO, DEBUG, debug, error, info, warning

def setup_logging(debug=False):
	if debug:
		basicConfig(format='[%(filename)s:%(lineno)s %(levelname)s] %(funcName)s: %(message)s',
					level=DEBUG)
	else:
		basicConfig(format='[%(levelname)s] %(message)s', level=INFO)

LOGD = debug
LOGE = error
LOGI = info
LOGW = warning
