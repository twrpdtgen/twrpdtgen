from pathlib import Path
from typing import Optional
from twrpdtgen import jinja_env

def render_template(device_tree_path: Optional[Path], template_file: str,
					out_file: str = '', to_file=True, **kwargs):
	template = jinja_env.get_template(template_file)
	rendered_template = template.render(**kwargs)
	if to_file:
		if not out_file:
			out_file = template_file.replace('.jinja2', '')
		with open(f"{device_tree_path}/{out_file}", 'w', encoding="utf-8") as out:
			out.write(rendered_template)
		return True
	else:
		return rendered_template
