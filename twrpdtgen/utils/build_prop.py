#
# Copyright (C) 2020 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from pathlib import Path
from typing import Union

class BuildProp:
	"""
	A class representing a build prop.

	This class basically mimics Android props system, with both getprop and setprop commands
	"""
	def __init__(self, file: Path):
		"""
		Create a dictionary containing all the key-value from a build prop.
		"""
		self.file = file.read_text()
		self.props = {}

		for prop in self.file.splitlines():
			if prop.startswith("#"):
				continue
			try:
				prop_name, prop_value = prop.split("=", 1)
			except ValueError:
				continue
			else:
				self.set_prop(prop_name, prop_value)
	
	def get_prop(self, prop: str) -> Union[str, None]:
		"""
		From a prop name, return the prop value.

		Returns a string if it exists, else None
		"""
		try:
			return self.props[prop]
		except KeyError:
			return None

	def set_prop(self, prop_name: str, prop_value: str):
		self.props[prop_name] = prop_value
