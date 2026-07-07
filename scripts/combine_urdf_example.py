"""Combine the Realman rm75_6f arm, the Robotiq 2F-85 gripper and a wrist camera,
then visualize the result.

This is a manual test/demo for :func:`airo_models.urdf.attach_urdf`. It attaches
the Robotiq gripper to the arm's ``tool0`` link (with a 2 cm z-offset) and mounts
an Intel RealSense D435 wrist camera 5 cm along the tool0 y-axis, tilted 30 degrees
downward so its optical axis points toward the gripper fingertips.  The merged URDF
is written to a temporary file and opened in the browser-based viser viewer
(reusing ``scripts/visualize_urdf.py``).

    python scripts/visualize_combined_arm_gripper.py

Then open the printed URL (default http://localhost:8080) in your browser.
The gripper joints are kept actuated so you can move the fingers with the GUI
sliders.

Requires the optional visualization dependencies::

    pip install airo-models[viz]
"""

import copy
import sys
from pathlib import Path

# Allow running from a git clone without having installed the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import visualize_urdf  # noqa: E402

import airo_models  # noqa: E402
from airo_models.urdf import attach_urdf, make_paths_absolute, read_urdf, write_urdf_to_tempfile  # noqa: E402


def build_combined_urdf() -> str:
    """Attach the Robotiq 2F-85 gripper and a D435 wrist camera to the rm75_6f arm."""
    arm_path = airo_models.get_urdf_path("rm75_6f")
    gripper_path = airo_models.get_urdf_path("robotiq_2f_85")
    camera_path = airo_models.get_urdf_path("d435")

    arm = read_urdf(arm_path)
    gripper = read_urdf(gripper_path)
    camera = read_urdf(camera_path)

    # The merged URDF is written to a temp dir, so every relative mesh path must
    # be made absolute. attach_urdf absolutizes attachments via attachment_urdf_path;
    # we absolutize the arm's paths here.
    make_paths_absolute(arm, arm_path)

    # attach_urdf modifies the arm dict in-place; pass copies so originals stay untouched.
    attach_urdf(
        arm,
        copy.deepcopy(gripper),
        parent_link="tool0",
        child_prefix="robotiq_",
        attachment_urdf_path=gripper_path,
        origin_xyz="0 0 0.01",  # 1 cm offset along the tool0 z-axis, emulate connector plate
        freeze_joints=False,  # keep the gripper fingers actuated
    )

    # Wrist camera: 5 cm along tool0 y-axis, tilted 30° (π/6) downward around the
    # x-axis so the optical axis (camera Z+) points toward the gripper fingertips.
    attach_urdf(
        arm,
        copy.deepcopy(camera),
        parent_link="tool0",
        child_prefix="d435_",
        attachment_urdf_path=camera_path,
        origin_xyz="0.02 0.05 0.06",
        origin_rpy="-0.3 0 3.14",  # +π/6 rad: tilts optical axis 30° toward -Y of tool0
    )

    combined_path = write_urdf_to_tempfile(arm, prefix="rm75_6f_robotiq_2f_85_d435_")
    return combined_path


def main() -> None:
    combined_path = build_combined_urdf()
    print(f"Combined URDF written to: {combined_path}")

    # Reuse the existing viser viewer by handing it the merged URDF path.
    sys.argv = [sys.argv[0], combined_path]
    visualize_urdf.main()


if __name__ == "__main__":
    main()
