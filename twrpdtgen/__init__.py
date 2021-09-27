from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path

__version__ = "2.0.1"

module_path = Path(__file__).parent
current_path = Path(os.getcwd())

jinja_env = Environment(loader=FileSystemLoader(module_path / 'templates'),
						autoescape=True, trim_blocks=True, lstrip_blocks=True)
