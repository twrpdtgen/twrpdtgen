# pylint: disable=too-many-locals, too-many-statements, too-many-branches

from logging import debug, info, warning, error
from pathlib import Path
from shutil import copyfile
from twrpdtgen import __version__ as version
from twrpdtgen.info_extractors.buildprop import BuildPropReader
from twrpdtgen.utils.aik_manager import AIKManager
from twrpdtgen.utils.build_prop import BuildProp
from twrpdtgen.utils.device_tree import DeviceTree
from twrpdtgen.utils.fstab import make_twrp_fstab
from twrpdtgen.utils.template import render_template

# Makes the linter happy
debug = debug
info = info
warning = warning
error = error

def generate_device_tree(recovery_image: Path, output_path: Path, is_debug=False) -> DeviceTree:
	"""
	Generate a TWRP-compatible device tree from a recovery image (or a boot image if the device is A/B)

	Returns a DeviceTree object if the generation went fine, else an integer
	"""
	if not recovery_image.is_file():
		raise FileNotFoundError("Specified file doesn't exist")

	aik = AIKManager(is_debug)
	aik.extract(recovery_image)

	debug("Getting device infos...")
	if aik.buildprop is None:
		raise AssertionError("Couldn't find any build.prop")
	debug("Using " + str(aik.buildprop) + " as build.prop")
	build_prop = BuildProp(aik.buildprop)
	props = BuildPropReader(build_prop)
	device_tree = DeviceTree(props, output_path)

	debug("Copying kernel...")
	# Create a new kernel name from arch
	kernel_names = {
		"arm": "zImage",
		"arm64": "Image.gz",
		"x86": "bzImage",
		"x86_64": "bzImage"
	}
	try:
		new_kernel_name = kernel_names[props.arch]
	except KeyError:
		new_kernel_name = "zImage"
	if props.arch in ("arm", "arm64") and (aik.dt_image is None and aik.dtb_image is None):
		new_kernel_name += "-dtb"

	if aik.kernel is not None:
		copyfile(aik.kernel, device_tree.prebuilt_path / new_kernel_name)
	if aik.dt_image is not None:
		copyfile(aik.dt_image, device_tree.dt_image)
	if aik.dtb_image is not None:
		copyfile(aik.dtb_image, device_tree.dtb_image)
	if aik.dtbo_image is not None:
		copyfile(aik.dtbo_image, device_tree.dtbo_image)

	if Path(aik.ramdisk_path / "etc" / "twrp.fstab").is_file():
		debug("Found a TWRP fstab, copying it...")
		copyfile(aik.ramdisk_path / "etc" / "twrp.fstab", device_tree.fstab)
	elif Path(aik.ramdisk_path / "etc" / "recovery.fstab").is_file():
		debug("Generating fstab...")
		make_twrp_fstab(aik.ramdisk_path / "etc" / "recovery.fstab",
						device_tree.fstab)
	elif Path(aik.ramdisk_path / "system" / "etc" / "recovery.fstab").is_file():
		debug("Generating fstab...")
		make_twrp_fstab(aik.ramdisk_path / "system" / "etc" / "recovery.fstab",
						device_tree.fstab)
	else:
		raise AssertionError("fstab not found")

	for file in aik.ramdisk_path.iterdir():
		if file.name.endswith(".rc") and file != "init.rc":
			copyfile(aik.ramdisk_path / file,
					 device_tree.recovery_root_path / file.name, follow_symlinks=True)

	debug("Creating Android.mk...")
	render_template(device_tree.path, "Android.mk.jinja2", device_codename=props.codename)

	debug("Creating AndroidProducts.mk...")
	render_template(device_tree.path, "AndroidProducts.mk.jinja2",
					device_codename=props.codename)

	debug("Creating BoardConfig.mk...")
	render_template(device_tree.path, "BoardConfig.mk.jinja2",
					device_manufacturer=props.manufacturer,
					device_codename=props.codename,
					device_is_ab=props.device_is_ab,
					device_platform=props.platform,
					device_arch=props.arch,
					board_name=aik.board_name,
					recovery_size=aik.recovery_size,
					cmdline=aik.cmdline,
					kernel=aik.kernel,
					kernel_name=new_kernel_name,
					dt_image=aik.dt_image,
					dtb_image=aik.dtb_image,
					dtbo_image=aik.dtbo_image,
					header_version=aik.header_version,
					base_address=aik.base_address,
					pagesize=aik.pagesize,
					ramdisk_offset=aik.ramdisk_offset,
					tags_offset=aik.tags_offset,
					ramdisk_compression=aik.ramdisk_compression,
					flash_block_size=str(int(aik.pagesize) * 64))

	debug("Creating device.mk...")
	render_template(device_tree.path, "device.mk.jinja2",
					device_codename=props.codename,
					device_manufacturer=props.manufacturer,
					device_platform=props.platform,
					device_is_ab=props.device_is_ab)

	debug(f"Creating omni_{props.codename}.mk...")
	render_template(device_tree.path, "omni.mk.jinja2", out_file=f"omni_{props.codename}.mk",
					device_codename=props.codename,
					device_manufacturer=props.manufacturer,
					device_brand=props.brand,
					device_model=props.model,
					device_has_64bit_arch=props.device_has_64bit_arch)

	debug("Creating vendorsetup.sh...")
	render_template(device_tree.path, "vendorsetup.sh.jinja2", device_codename=props.codename)

	git_config_reader = device_tree.git_repo.config_reader()
	git_config_writer = device_tree.git_repo.config_writer()
	try:
		git_global_email, git_global_name = git_config_reader.get_value('user', 'email'), git_config_reader.get_value('user', 'name')
	except:
		git_global_email, git_global_name = None, None
	if git_global_email is None or git_global_name is None:
		git_config_writer.set_value('user', 'email', 'barezzisebastiano@gmail.com')
		git_config_writer.set_value('user', 'name', 'Sebastiano Barezzi')
	device_tree.git_repo.index.add(["*"])
	commit_message = render_template(None, "commit_message.jinja2", to_file=False,
									 device_codename=props.codename,
									 device_arch=props.arch,
									 device_manufacturer=props.manufacturer,
									 device_brand=props.brand,
									 device_model=props.model,
									 version=version)
	device_tree.git_repo.index.commit(commit_message)

	# Cleanup
	aik.cleanup()

	return device_tree
