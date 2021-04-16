#!/usr/bin/python3

import json
from natsort import natsorted
import requests
import toml

FILE = "pyproject.toml"

def get_new_versions(package_name):
	print(f"Getting versions for {package_name}")
	url = f"https://pypi.org/pypi/{package_name}/json"
	response = requests.get(url).text
	data = dict(json.loads(response))
	versions = list(data["releases"].keys())
	valid_versions = natsorted(versions)
	return valid_versions[-1]

def main():
	with open(FILE, 'r') as file:
		pyproject_text = file.read()
		file.seek(0)
		pyproject_list = file.readlines()
		file.close()

	pyproject_dict = toml.loads(pyproject_text, dict)

	dependencies = pyproject_dict["tool"]["poetry"]["dependencies"]
	for dependency in dependencies:
		old_version = dependencies[dependency][1:]
		try:
			new_version = get_new_versions(dependency)
		except:
			new_version = old_version

		print(f"{dependency}: old: {old_version}, new: {new_version}")
		dependencies[dependency] = new_version

	for line in range(len(pyproject_list)):
		if pyproject_list[line].split() == []:
			continue
		maybe_dep = pyproject_list[line].split()[0]
		if maybe_dep in dependencies:
			pyproject_list[line] = f'{maybe_dep} = "^{dependencies[maybe_dep]}"\n'

	with open(FILE, 'w') as f:
		f.writelines(pyproject_list)
		f.close()

main()
