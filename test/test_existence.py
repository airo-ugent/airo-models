import os

from airo_models.utils import AIRO_MODEL_NAMES, get_urdf_path


def test_existence():
    """Test whether the URDF files were included in the pip install.

    Try this test with both:
    pip install -e .
    pip install .
    """
    for name in AIRO_MODEL_NAMES:
        urdf_path = get_urdf_path(name)
        assert os.path.exists(urdf_path), f"URDF file for {name} does not exist at {urdf_path}"
