import os

import airo_models


def test_existence():
    """Test whether the URDF files were included in the pip install.

    Try this test with both:
    pip install -e .
    pip install .
    """
    for name in airo_models.AIRO_MODEL_NAMES:
        urdf_path = airo_models.get_urdf_path(name)
        assert os.path.exists(urdf_path), f"URDF file for {name} does not exist at {urdf_path}"

    # Also test long-form import
    for name in airo_models.files.AIRO_MODEL_NAMES:
        urdf_path = airo_models.files.get_urdf_path(name)
        assert os.path.exists(urdf_path), f"URDF file for {name} does not exist at {urdf_path}"
