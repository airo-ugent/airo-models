"""
sanity check for arm URDFs.
FK_urdf(joint_config) should match the actual pose of tool0 in base frame as reported by a real robot.
If this is not the case the URDF is likely wrong.
"""

import ast
from pathlib import Path

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


def _fk_tool0_matrix(robot, joint_angles_rad: list[float]) -> np.ndarray:
    """Return tool0 pose as a 4x4 homogeneous matrix (translation in metres).

    The UR5e URDF defines base_link (ROS convention root) with two fixed
    children both rotated 180° about Z: base_link_inertia (kinematic chain
    root) and base (the robot's physical Base coordinate frame).  The reference
    poses recorded on a real robot use the "base" frame, so we compute the
    transform base -> tool0.
    """
    import jax.numpy as jnp

    link_names = list(robot.links.names)
    tool0_idx = link_names.index("tool0")
    base_idx = link_names.index("base")

    cfg = jnp.array(joint_angles_rad)
    fk = robot.forward_kinematics(cfg)

    def wxyz_xyz_to_matrix(wxyz_xyz: np.ndarray) -> np.ndarray:
        R = Rotation.from_quat(wxyz_xyz[[1, 2, 3, 0]]).as_matrix()
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = wxyz_xyz[4:]
        return T

    T_base = wxyz_xyz_to_matrix(np.array(fk[base_idx]))
    T_tool0 = wxyz_xyz_to_matrix(np.array(fk[tool0_idx]))
    return np.linalg.inv(T_base) @ T_tool0


def _load_poses_txt(path: Path) -> list[tuple[list[float], np.ndarray]]:
    """Parse a poses .txt file where each non-comment line is semicolon-separated Python literals."""
    cases = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(";")
        cases.append(tuple(ast.literal_eval(p) for p in parts))
    return cases


def _load_ur5e_poses(path: Path) -> list[tuple[list[float], np.ndarray]]:
    """Parse ur5e_poses.txt: each non-comment line is 'joints_list;matrix_list'.

    Source: https://github.com/Victorlouisdg/ur-analytic-ik/blob/main/tests/data/ur5e_poses.txt
    Returns a list of (joint_angles_rad[6], 4x4 homogeneous matrix).
    """
    cases = []
    for joints, matrix in _load_poses_txt(path):
        cases.append((joints, np.array(matrix)))
    return cases


def _load_rm75_6f_poses(path: Path) -> list[tuple[list[float], list[float], list[float]]]:
    """Parse rm75_6f_poses.txt: each non-comment line is 'joints_deg;xyz_mm;rpy_rad'.

    Returns a list of (joint_angles_deg[7], tcp_xyz_mm[3], tcp_rpy_rad[3]).
    """
    return _load_poses_txt(path)


_DATA_DIR = Path(__file__).parent / "data"
_UR5E_TEST_CASES = _load_ur5e_poses(_DATA_DIR / "ur5e_poses.txt")

# tcp_rpy_rad is (RX, RY, RZ) from the Realman UI = ZYX Euler (roll, pitch, yaw).
_ORIENTATION_TOL_RAD = 0.01
_RM75_FK_TEST_CASES = _load_rm75_6f_poses(_DATA_DIR / "rm75_6f_poses.txt")


@pytest.mark.parametrize("joint_angles_deg,expected_xyz_mm,expected_rpy_rad", _RM75_FK_TEST_CASES)
def test_rm75_6f_fk(joint_angles_deg, expected_xyz_mm, expected_rpy_rad):
    robot = _load_pyroki_robot("rm75_6f")
    xyz_mm, rpy_rad = _fk_tool0_xyz_rpy(robot, joint_angles_deg)
    np.testing.assert_allclose(xyz_mm, expected_xyz_mm, atol=0.01)
    np.testing.assert_allclose(rpy_rad, expected_rpy_rad, atol=_ORIENTATION_TOL_RAD)


@pytest.mark.parametrize("joint_angles_rad,expected_matrix", _UR5E_TEST_CASES)
def test_ur5e_fk(joint_angles_rad, expected_matrix):
    # Reference poses were recorded on a real UR5e robot (base -> tool0 frames),
    # so a ~1 cm / ~0.01 tolerance accounts for the URDF model vs physical arm.
    robot = _load_pyroki_robot("ur5e")
    T = _fk_tool0_matrix(robot, joint_angles_rad)
    np.testing.assert_allclose(T, expected_matrix, atol=0.01)


def test_ur3e_fk():
    pass
