import os

AIRO_MODEL_NAMES = ["ur3e", "ur5e", "robotiq_2f_85"]


def get_urdf_path(name: str) -> str:
    """Get the absolute path to a URDF file using a name e.g. "ur5e".

    Args:
        name: the name of robot or gripper you want the URDF file for

    Returns:
        urdf_path: the absolute path to the URDF file
    """

    airo_models_dir = os.path.dirname(__file__)

    name_to_urdf_path = {
        "ur3e": os.path.join(airo_models_dir, "arms", "ur3e", "ur3e.urdf"),
        "ur5e": os.path.join(airo_models_dir, "arms", "ur5e", "ur5e.urdf"),
        "robotiq_2f_85": os.path.join(airo_models_dir, "grippers", "robotiq_2f_85", "urdf", "robotiq_2f_85.urdf"),
        "schunk_egk40": os.path.join(airo_models_dir, "grippers", "schunk_egk40", "urdf", "schunk_egk40.urdf"),
        "schunk_egk40_magneto": os.path.join(
            airo_models_dir, "grippers", "schunk_egk40_magneto", "schunk_egk40_magneto.urdf"
        ),
        "kelo_robile": os.path.join(airo_models_dir, "mobile_platforms", "kelo_robile", "urdf", "mobi.urdf"),
        "kelo_robile_battery": os.path.join(
            airo_models_dir, "mobile_platforms", "kelo_robile", "urdf", "battery_brick.urdf"
        ),
        "kelo_robile_cpu": os.path.join(airo_models_dir, "mobile_platforms", "kelo_robile", "urdf", "cpu_brick.urdf"),
        "kelo_robile_wheel": os.path.join(
            airo_models_dir, "mobile_platforms", "kelo_robile", "urdf", "wheel_brick.urdf"
        ),
        "zed2i": os.path.join(airo_models_dir, "cameras", "zed", "zed2i.urdf"),
        "zedm": os.path.join(airo_models_dir, "cameras", "zed", "zedm.urdf"),
        "d435": os.path.join(airo_models_dir, "cameras", "realsense", "d435", "d435.urdf"),
        "table8080": os.path.join(airo_models_dir, "environment", "tables", "table8080.urdf"),
        "mounting_plate_ur3e": os.path.join(
            airo_models_dir, "environment", "mounting_plates", "mounting_plate_ur3e.urdf"
        ),
        "mounting_plate_ur5e": os.path.join(
            airo_models_dir, "environment", "mounting_plates", "mounting_plate_ur5e.urdf"
        ),
    }

    if name in name_to_urdf_path:
        urdf_path = os.path.abspath(name_to_urdf_path[name])
        return urdf_path
    else:
        raise ValueError(f"We have no URDF for name: {name}")


if __name__ == "__main__":
    for name in AIRO_MODEL_NAMES:
        print(f"{name}: {get_urdf_path(name)}")
