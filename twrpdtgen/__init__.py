from pathlib import Path
from jinja2 import Environment, FileSystemLoader

__version__ = "1.1.0"

current_path = Path(__file__).parent.parent
aik_path = current_path / "extract"
working_path = current_path / "working"

jinja_env = Environment(loader=FileSystemLoader(current_path / 'templates'),
                        autoescape=True, trim_blocks=True, lstrip_blocks=True)
