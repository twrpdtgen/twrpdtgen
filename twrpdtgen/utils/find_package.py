import shutil

def find_package(packageName):
  return shutil.which(packageName) is not None
  