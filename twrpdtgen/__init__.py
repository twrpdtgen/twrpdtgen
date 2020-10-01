from pathlib import Path

__version__ = "1.0.0"

current_path = Path(__file__).parent.parent
aik_path = current_path / "extract"
aik_images_path = aik_path / "split_img"
aik_ramdisk_path = aik_path / "ramdisk"
working_path = current_path / "working"
