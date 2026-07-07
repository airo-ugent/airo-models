"""
sanity check for arm URDFs. FK(joint_config) should match the expected pose of tool0 in base frame, if not then the URDF is likely wrong.
"""

import numpy as np
import pytest
import yourdfpy
from scipy.spatial.transform import Rotation

import airo_models


def _load_pyroki_robot(urdf_name: str):
    import pyroki as pk

    urdf_path = airo_models.get_urdf_path(urdf_name)
    urdf = yourdfpy.URDF.load(str(urdf_path))
    return pk.Robot.from_urdf(urdf)


def _fk_tool0_xyz_rpy(robot, joint_angles_deg: list[float]) -> tuple[np.ndarray, np.ndarray]:
    """Return tool0 position (mm) and RPY orientation (rad, ZYX Euler: roll=RX, pitch=RY, yaw=RZ)."""
    import jax.numpy as jnp

    tool0_idx = list(robot.links.names).index("tool0")
    cfg = jnp.deg2rad(jnp.array(joint_angles_deg))
    fk = robot.forward_kinematics(cfg)
    wxyz_xyz = np.array(fk[tool0_idx])
    xyz_mm = wxyz_xyz[4:] * 1000.0
    # pyroki uses wxyz convention; scipy uses xyzw
    r = Rotation.from_quat(wxyz_xyz[[1, 2, 3, 0]])
    # as_euler('ZYX') returns [yaw, pitch, roll]; reverse to get [roll, pitch, yaw] = [RX, RY, RZ]
    rpy = r.as_euler("ZYX")[::-1]
    return xyz_mm, rpy


# These config-pose combinations were collected from the Realman control UI (screenshots).
# tcp_rpy_rad is (RX, RY, RZ) from the Realman UI = ZYX Euler (roll, pitch, yaw).
_ORIENTATION_TOL_RAD = 0.01

# Each entry: (joint_angles_deg[7], tcp_xyz_mm[3], tcp_rpy_rad[3])
_RM75_FK_TEST_CASES = [
    (
        [-13.152, 39.428, -35.966, 69.564, -154.992, -78.321, 89.994],
        [301.337, -182.199, 232.684],
        [3.131, 0.043, -2.407],
    ),
    (
        [-96.45, 2.389, -164.038, 90.346, -163.519, 23.722, 89.993],
        [-42.518, 342.673, 570.810],
        [-1.121, 0.275, 0.175],
    ),
    (
        [-43.418, 38.982, -126.452, 65.982, -158.848, -38.713, 89.993],
        [-164.606, -256.020, 589.512],
        [-1.494, -0.274, 1.913],
    ),
]


@pytest.mark.parametrize("joint_angles_deg,expected_xyz_mm,expected_rpy_rad", _RM75_FK_TEST_CASES)
def test_rm75_6f_fk(joint_angles_deg, expected_xyz_mm, expected_rpy_rad):
    robot = _load_pyroki_robot("rm75_6f")
    xyz_mm, rpy_rad = _fk_tool0_xyz_rpy(robot, joint_angles_deg)
    np.testing.assert_allclose(xyz_mm, expected_xyz_mm, atol=0.01)
    np.testing.assert_allclose(rpy_rad, expected_rpy_rad, atol=_ORIENTATION_TOL_RAD)


def test_ur3e_fk():
    pass


def test_ur5e_fk():
    pass