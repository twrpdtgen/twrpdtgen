#
# Copyright (C) 2022 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from twrpdtgen import module_path

jinja_env = Environment(loader=FileSystemLoader(module_path / 'templates'),
                        autoescape=True, trim_blocks=True, lstrip_blocks=True)

def render_template(path: Optional[Path], template_file: str,
                    out_file: str = '', to_file=True, **kwargs):
	template = jinja_env.get_template(f"{template_file}.jinja2")
	rendered_template = template.render(**kwargs)

	if to_file:
		if not out_file:
			out_file = template_file

		with open(f"{path}/{out_file}", 'w', encoding="utf-8") as out:
			out.write(rendered_template)

	return rendered_template
