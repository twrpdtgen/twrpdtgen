import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

__version__ = "1.2.5"

module_path = Path(__file__).parent
current_path = Path(os.getcwd())

jinja_env = Environment(loader=FileSystemLoader(module_path / 'templates'),
						autoescape=True, trim_blocks=True, lstrip_blocks=True)
