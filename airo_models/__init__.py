# init files are still required in modern python!
# https://peps.python.org/pep-0420/ introduced implicit namespace packages
# but for building and many toolings, you still need to have __init__ files (at least in the root of the package).
# e.g. if you remove this init file and try to build with pip install .
# you won't be able to import the dummy module.
from .files import AIRO_MODEL_NAMES, get_urdf_path

__all__ = ["get_urdf_path", "AIRO_MODEL_NAMES"]
