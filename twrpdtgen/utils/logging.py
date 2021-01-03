from logging import basicConfig, INFO, DEBUG

def setup_logging(verbose=False):
	if verbose:
		basicConfig(format='[%(asctime)s] [%(filename)s:%(lineno)s %(levelname)s] %(funcName)s: %(message)s',
					level=DEBUG)
	else:
		basicConfig(format='[%(levelname)s] %(message)s', level=INFO)
