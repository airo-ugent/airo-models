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
    }

    if name in name_to_urdf_path:
        urdf_path = os.path.abspath(name_to_urdf_path[name])
        return urdf_path
    else:
        raise ValueError(f"We have no URDF for name: {name}")


if __name__ == "__main__":
    for name in AIRO_MODEL_NAMES:
        print(f"{name}: {get_urdf_path(name)}")
