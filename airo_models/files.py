import os


AIRO_MODELS_DIR = os.path.dirname(__file__)

MODEL_NAME_TO_URDF_PATH = {
    "ur3e": os.path.join(AIRO_MODELS_DIR, "arms", "ur3e", "ur3e.urdf"),
    "ur5e": os.path.join(AIRO_MODELS_DIR, "arms", "ur5e", "ur5e.urdf"),
    "ur5e_convex_collisions": os.path.join(AIRO_MODELS_DIR, "arms", "ur5e", "ur5e_convex_collisions.urdf"),
    "rm75_6f": os.path.join(AIRO_MODELS_DIR, "arms", "rm75_6f", "rm75_6f.urdf"),
    "rm75_6f_primitives": os.path.join(AIRO_MODELS_DIR, "arms", "rm75_6f", "rm75_6f_primitives.urdf"),
    "robotiq_2f_85": os.path.join(AIRO_MODELS_DIR, "grippers", "robotiq_2f_85", "urdf", "robotiq_2f_85.urdf"),
    "schunk_egk40": os.path.join(AIRO_MODELS_DIR, "grippers", "schunk_egk40", "urdf", "schunk_egk40.urdf"),
    "schunk_egk40_magneto": os.path.join(
        AIRO_MODELS_DIR, "grippers", "schunk_egk40_magneto", "schunk_egk40_magneto.urdf"
    ),
    "kelo_robile": os.path.join(AIRO_MODELS_DIR, "mobile_platforms", "kelo_robile", "urdf", "mobi.urdf"),
    "kelo_robile_battery": os.path.join(
        AIRO_MODELS_DIR, "mobile_platforms", "kelo_robile", "urdf", "battery_brick.urdf"
    ),
    "kelo_robile_cpu": os.path.join(AIRO_MODELS_DIR, "mobile_platforms", "kelo_robile", "urdf", "cpu_brick.urdf"),
    "kelo_robile_wheel": os.path.join(AIRO_MODELS_DIR, "mobile_platforms", "kelo_robile", "urdf", "wheel_brick.urdf"),
    "zed2i": os.path.join(AIRO_MODELS_DIR, "cameras", "zed", "zed2i.urdf"),
    "zedm": os.path.join(AIRO_MODELS_DIR, "cameras", "zed", "zedm.urdf"),
    "d435": os.path.join(AIRO_MODELS_DIR, "cameras", "realsense", "d435", "d435.urdf"),
    "table8080": os.path.join(AIRO_MODELS_DIR, "environment", "tables", "table8080.urdf"),
    "mounting_plate_ur3e": os.path.join(AIRO_MODELS_DIR, "environment", "mounting_plates", "mounting_plate_ur3e.urdf"),
    "mounting_plate_ur5e": os.path.join(AIRO_MODELS_DIR, "environment", "mounting_plates", "mounting_plate_ur5e.urdf"),
}


AIRO_MODEL_NAMES = list(MODEL_NAME_TO_URDF_PATH.keys())


def get_urdf_path(name: str) -> str:
    """Get the absolute path to a URDF file using a name e.g. "ur5e".

    Args:
        name: the name of robot or gripper you want the URDF file for

    Returns:
        urdf_path: the absolute path to the URDF file
    """

    if name in MODEL_NAME_TO_URDF_PATH:
        urdf_path = os.path.abspath(MODEL_NAME_TO_URDF_PATH[name])
        return urdf_path
    else:
        raise ValueError(f"We have no URDF for name: {name}")


if __name__ == "__main__":
    for name in AIRO_MODEL_NAMES:
        print(f"{name}: {get_urdf_path(name)}")
