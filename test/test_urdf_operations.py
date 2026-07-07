import airo_models
from airo_models.urdf import attach_urdf, read_urdf


def check_key_in_urdf(dict_: dict, key: str):
    """Check if a key is in a URDF dictionary."""
    for k, v in dict_.items():
        if k == key:
            return True
        elif isinstance(v, dict):
            if check_key_in_urdf(v, key):
                return True
        elif isinstance(v, list):
            for d in v:
                if check_key_in_urdf(d, key):
                    return True
    return False


def test_delete_key():
    """Test keys are deleted correctly from URDF dictionaries."""
    delete_test_dict = {
        "a": "1",
        "b": {
            "c": "2",
            "d": [{"f": "3"}, {"c": "4"}],
        },
        "e": 5,
    }

    airo_models.urdf.delete_key(delete_test_dict, "c")

    assert check_key_in_urdf(delete_test_dict, "a")
    assert check_key_in_urdf(delete_test_dict, "b")
    assert not check_key_in_urdf(delete_test_dict, "c")
    assert check_key_in_urdf(delete_test_dict, "d")
    assert check_key_in_urdf(delete_test_dict, "e")
    assert check_key_in_urdf(delete_test_dict, "f")


def _simple_urdf(name: str, link_name: str = "base_link") -> dict:
    """Return a minimal single-link URDF dict for testing."""
    return {
        "robot": {
            "@name": name,
            "link": {"@name": link_name},
        }
    }


def _urdf_with_joint(name: str, joint_type: str = "revolute") -> dict:
    """Return a two-link URDF dict with one joint."""
    return {
        "robot": {
            "@name": name,
            "link": [{"@name": "base_link"}, {"@name": "end_link"}],
            "joint": {
                "@name": "base_to_end",
                "@type": joint_type,
                "parent": {"@link": "base_link"},
                "child": {"@link": "end_link"},
                "axis": {"@xyz": "0 0 1"},
                "limit": {"@lower": "-1", "@upper": "1", "@effort": "10", "@velocity": "1"},
            },
        }
    }


def test_attach_urdf_links_and_joints_merged():
    """Attached links and joints should appear in the base URDF."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _simple_urdf("gripper")

    attach_urdf(base, attachment, parent_link="tool0", child_prefix="g_")

    link_names = {link["@name"] for link in base["robot"]["link"]}
    joint_names = {j["@name"] for j in base["robot"]["joint"]}

    assert "tool0" in link_names
    assert "g_base_link" in link_names
    assert "tool0_to_g" in joint_names


def test_attach_urdf_prefix_applied():
    """All attachment link/joint names must be prefixed."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _urdf_with_joint("gripper")

    attach_urdf(base, attachment, parent_link="tool0", child_prefix="schunk_")

    link_names = {link["@name"] for link in base["robot"]["link"]}
    joint_names = {j["@name"] for j in base["robot"]["joint"]}

    assert "schunk_base_link" in link_names
    assert "schunk_end_link" in link_names
    assert "schunk_base_to_end" in joint_names
    # Original unprefixed names must not appear
    assert "base_link" not in link_names
    assert "end_link" not in link_names


def test_attach_urdf_freeze_joints():
    """freeze_joints=True must convert all attachment joints to fixed."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _urdf_with_joint("gripper", joint_type="revolute")

    attach_urdf(base, attachment, parent_link="tool0", child_prefix="g_", freeze_joints=True)

    for joint in base["robot"]["joint"]:
        assert joint["@type"] == "fixed", f"Joint {joint['@name']} is not fixed"


def test_attach_urdf_no_freeze():
    """freeze_joints=False must preserve the original joint types."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _urdf_with_joint("gripper", joint_type="revolute")

    attach_urdf(base, attachment, parent_link="tool0", child_prefix="g_", freeze_joints=False)

    joint_types = {j["@name"]: j["@type"] for j in base["robot"]["joint"]}
    assert joint_types["g_base_to_end"] == "revolute"


def test_attach_urdf_custom_root_link():
    """child_root_link should override the default 'base_link' root."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _simple_urdf("sensor", link_name="sensor_mount")

    attach_urdf(base, attachment, parent_link="tool0", child_prefix="s_", child_root_link="sensor_mount")

    joint_names = {j["@name"]: j for j in base["robot"]["joint"]}
    attaching_joint = joint_names["tool0_to_s"]
    assert attaching_joint["child"]["@link"] == "s_sensor_mount"


def test_attach_urdf_origin():
    """The attaching joint should carry the requested xyz/rpy."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _simple_urdf("camera")

    attach_urdf(
        base,
        attachment,
        parent_link="tool0",
        child_prefix="cam_",
        origin_xyz="0 -0.06 -0.04",
        origin_rpy="0 1.5708 0",
    )

    attaching_joint = next(j for j in base["robot"]["joint"] if j["@name"] == "tool0_to_cam")
    assert attaching_joint["origin"]["@xyz"] == "0 -0.06 -0.04"
    assert attaching_joint["origin"]["@rpy"] == "0 1.5708 0"


def _urdf_with_extras(name: str) -> dict:
    """Two-link URDF with a mimic reference and a robot-level transmission."""
    return {
        "robot": {
            "@name": name,
            "link": [{"@name": "base_link"}, {"@name": "end_link"}],
            "joint": {
                "@name": "drive_joint",
                "@type": "revolute",
                "parent": {"@link": "base_link"},
                "child": {"@link": "end_link"},
                "mimic": {"@joint": "drive_joint", "@multiplier": "1", "@offset": "0"},
            },
            "transmission": {
                "@name": "drive_trans",
                "joint": {"@name": "drive_joint"},
                "actuator": {"@name": "drive_motor"},
            },
        }
    }


def test_attach_urdf_copies_extra_elements():
    """Robot-level elements other than link/joint should be copied by default."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _urdf_with_extras("gripper")

    attach_urdf(base, attachment, parent_link="tool0", child_prefix="g_", freeze_joints=False)

    assert "transmission" in base["robot"]
    transmission = base["robot"]["transmission"][0]
    # References to the (now prefixed) joint must be updated inside the transmission.
    assert transmission["joint"]["@name"] == "g_drive_joint"


def test_attach_urdf_renames_mimic_reference():
    """mimic joint references must be updated to the prefixed joint name."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _urdf_with_extras("gripper")

    attach_urdf(base, attachment, parent_link="tool0", child_prefix="g_", freeze_joints=False)

    drive_joint = next(j for j in base["robot"]["joint"] if j["@name"] == "g_drive_joint")
    assert drive_joint["mimic"]["@joint"] == "g_drive_joint"


def test_attach_urdf_copy_extra_elements_disabled():
    """copy_extra_elements=False should merge only links and joints."""
    base = _simple_urdf("arm", link_name="tool0")
    attachment = _urdf_with_extras("gripper")

    attach_urdf(
        base,
        attachment,
        parent_link="tool0",
        child_prefix="g_",
        freeze_joints=False,
        copy_extra_elements=False,
    )

    assert "transmission" not in base["robot"]


def test_attach_urdf_with_real_models():
    """Smoke test: attach schunk + d435 to rm75_6f using actual airo-models URDFs."""
    arm_path = airo_models.get_urdf_path("rm75_6f")
    gripper_path = airo_models.get_urdf_path("schunk_egk40")
    camera_path = airo_models.get_urdf_path("d435")

    arm = read_urdf(arm_path)
    gripper = read_urdf(gripper_path)
    camera = read_urdf(camera_path)

    attach_urdf(arm, gripper, "tool0", "schunk_", attachment_urdf_path=gripper_path)
    attach_urdf(arm, camera, "tool0", "d435_", attachment_urdf_path=camera_path, origin_xyz="0 -0.06 -0.04")

    link_names = {link["@name"] for link in arm["robot"]["link"]}
    joint_names = {j["@name"] for j in arm["robot"]["joint"]}

    assert "schunk_base_link" in link_names
    assert "d435_base_link" in link_names
    assert "tool0_to_schunk" in joint_names
    assert "tool0_to_d435" in joint_names
