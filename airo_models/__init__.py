# init files are still required in modern python!
# https://peps.python.org/pep-0420/ introduced implicit namespace packages
# but for building and many toolings, you still need to have __init__ files (at least in the root of the package).
# e.g. if you remove this init file and try to build with pip install .
# you won't be able to import the dummy module.
import airo_models.primitives as primitives  # noqa: F401
import airo_models.urdf as urdf  # noqa: F401
from airo_models.primitives.box import *  # noqa: F401, F403
from airo_models.primitives.cylinder import *  # noqa: F401, F403
from airo_models.primitives.mesh import *  # noqa: F401, F403
from airo_models.primitives.sphere import *  # noqa: F401, F403

# Not sure if this relative import is needed. Should investigate.
from .files import AIRO_MODEL_NAMES, get_urdf_path

__all__ = ["urdf", "get_urdf_path", "AIRO_MODEL_NAMES"]
