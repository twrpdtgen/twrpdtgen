from pathlib import Path
from jinja2 import Environment, FileSystemLoader

__version__ = "1.1.0"

module_path = Path(__file__).parent
current_path = module_path.parent
aik_path = current_path / "extract"

jinja_env = Environment(loader=FileSystemLoader(module_path / 'templates'),
                        autoescape=True, trim_blocks=True, lstrip_blocks=True)
