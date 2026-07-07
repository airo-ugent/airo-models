"""Reading, writing and recurvise operations for URDFs, such as deleting keys or replacing values."""

import os
import tempfile

import xmltodict


def read_urdf(urdf_path: str) -> dict:
    """Reads a URDF (xml) file into a Python dictionary.
    Childern elements can be accessed by using the tag name as key e.g. urdf["robot"].
    Attributes can be accessed by using the "@" prefix e.g. link["@name"].

    Args:
        urdf_path: path to the URDF file.

    Returns:
        The URDF as a dictionary.
    """
    with open(urdf_path, "r") as file:
        xml_content = file.read()
    urdf = xmltodict.parse(xml_content)
    return urdf


def write_urdf_to_file(dict_: dict, urdf_path: str) -> None:
    urdf_str = dict_to_xml_str(dict_)
    with open(urdf_path, "w") as f:
        f.write(urdf_str)


def write_urdf_to_tempfile(dict_: dict, original_urdf_path: str | None = None, prefix: str = "urdf_model_") -> str:
    if original_urdf_path is not None:
        make_paths_absolute(dict_, original_urdf_path)
    urdf_str = dict_to_xml_str(dict_)
    urdf_file = tempfile.NamedTemporaryFile(prefix=prefix, suffix=".urdf", delete=False)
    urdf_file.write(urdf_str.encode())
    urdf_path = urdf_file.name
    return urdf_path


def dict_to_xml_str(dict_: dict) -> str:
    if not dict_:
        return ""
    return xmltodict.unparse(dict_, pretty=True, indent="  ", short_empty_elements=True)


def delete_key(dict_: dict, key: str) -> None:
    for k, v in list(dict_.items()):
        if k == key:
            del dict_[k]
        # Recurse
        elif isinstance(v, dict):
            delete_key(v, key)
        elif isinstance(v, list):
            for i in v:
                delete_key(i, key)


def replace_value(dict_: dict, key: str, value: str, new_value: str) -> None:
    for k, v in dict_.items():
        if key == key and v == value:
            dict_[k] = new_value
        # Recurse
        elif isinstance(v, dict):
            replace_value(v, key, value, new_value)
        elif isinstance(v, list):
            for d in v:
                replace_value(d, key, value, new_value)


def make_path_absolute(rel_path: str, urdf_path: str) -> str:
    return os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(urdf_path)), rel_path))


def make_paths_absolute(dict_: dict, urdf_path: str) -> None:
    for key, value in dict_.items():
        if key == "@filename" and not os.path.isabs(value):
            dict_[key] = make_path_absolute(value, urdf_path)
        # Recurse
        elif isinstance(value, dict):
            make_paths_absolute(value, urdf_path)
        elif isinstance(value, list):
            for item in value:
                make_paths_absolute(item, urdf_path)


def single_link_urdf_dict(name: str, geometry_dict: dict, material_dict: dict) -> dict:
    """Generate the basic structure of URDF for a single link with a given geometry.

    Corresponds to this URDF:
    ```xml
    <robot name="name">
        <link name="base_link">
            <visual>
                <geometry>
                    ...
                </geometry>
            </visual>
            <collision>
                <geometry>
                    ...
                </geometry>
            </collision>
        </link>
    </robot>
    ```

    Used by the functions that generate URDF primitives.
    """
    return {
        "robot": {
            "@name": name,
            "link": {
                "@name": "base_link",
                "visual": {"geometry": geometry_dict, "material": material_dict},
                "collision": {"geometry": geometry_dict},
            },
        }
    }


def make_static(dict_: dict) -> None:
    """Make all joints in the URDF fixed and remove mimic and transmission keys."""

    joint_types = ["revolute", "continuous", "prismatic", "floating", "planar"]
    for joint_type in joint_types:
        replace_value(dict_, "@type", joint_type, "fixed")

    delete_key(dict_, "mimic")
    delete_key(dict_, "transmission")


def _get_robot_element_by_name(urdf_dict: dict, element_type: str, element_name: str) -> dict | None:
    """Searches for a URDF link or joint with the specified name.
    Args:
        urdf_dict: A dictionary containing the parsed URDF data.
        element_type: The type of element to search for ('link' or 'joint').
        element_name: The name of the element to find.

    Returns:
        The URDF element dictionary if found, otherwise None.
    """
    if element_type not in ["link", "joint"]:
        raise ValueError("Invalid element_type. Must be 'link' or 'joint'")

    for element in urdf_dict["robot"][element_type]:
        if element["@name"] == element_name:
            return element
    return None  # Element not found


def get_link_by_name(urdf_dict: dict, link_name: str) -> dict | None:
    """Searches for a URDF link with the specified name.

    Args:
        urdf_dict: A dictionary containing the parsed URDF data.
        link_name: The name of the link to find.

    Returns:
        The URDF link dictionary if found, otherwise None.
    """
    return _get_robot_element_by_name(urdf_dict, "link", link_name)


def get_joint_by_name(urdf_dict: dict, joint_name: str) -> dict | None:
    """Searches for a URDF joint with the specified name.

    Args:
        urdf_dict: A dictionary containing the parsed URDF data.
        joint_name: The name of the joint to find.

    Returns:
        The URDF joint dictionary if found, otherwise None.
    """
    return _get_robot_element_by_name(urdf_dict, "joint", joint_name)


def material_dict(rgba: tuple[float, float, float, float]) -> dict:
    material_dict = {"color": {"@rgba": " ".join(map(str, rgba))}}
    return material_dict


def _collect_link_joint_names(urdf_dict: dict) -> set[str]:
    """Return the set of all link and joint names in a URDF dict."""
    robot = urdf_dict["robot"]
    names: set[str] = set()
    for section in ("link", "joint"):
        items = robot.get(section, [])
        if isinstance(items, dict):
            items = [items]
        for item in items:
            names.add(item["@name"])
    return names


def _rename_references(node: object, rename_map: dict[str, str]) -> None:
    """Recursively replace any string value that matches a key in *rename_map*.

    Used to update references to link/joint names (e.g. ``<mimic joint="...">``,
    ``<transmission><joint name="...">`` or drake collision-filter members) so
    they point at the prefixed names after :func:`_prefix_urdf_names`.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                if value in rename_map:
                    node[key] = rename_map[value]
            else:
                _rename_references(value, rename_map)
    elif isinstance(node, list):
        for item in node:
            _rename_references(item, rename_map)


def _prefix_urdf_names(urdf_dict: dict, prefix: str) -> None:
    """Prefix all link and joint names (and their parent/child references) in-place.

    Args:
        urdf_dict: Parsed URDF dictionary to modify in-place.
        prefix: String to prepend to every link and joint name.
    """
    robot = urdf_dict["robot"]
    for section in ("link", "joint"):
        items = robot.get(section, [])
        if isinstance(items, dict):
            robot[section] = [items]
        for item in robot.get(section, []):
            item["@name"] = prefix + item["@name"]
            if section == "joint":
                item["parent"]["@link"] = prefix + item["parent"]["@link"]
                item["child"]["@link"] = prefix + item["child"]["@link"]


def _ensure_list(urdf_dict: dict, key: str) -> None:
    """Ensure that robot[key] is a list (not a bare dict for single-element URDFs)."""
    robot = urdf_dict["robot"]
    if key not in robot:
        robot[key] = []
    elif isinstance(robot[key], dict):
        robot[key] = [robot[key]]


def attach_urdf(
    base_dict: dict,
    attachment_dict: dict,
    parent_link: str,
    child_prefix: str,
    child_root_link: str = "base_link",
    attachment_urdf_path: str | None = None,
    origin_xyz: str = "0 0 0",
    origin_rpy: str = "0 0 0",
    freeze_joints: bool = True,
    copy_extra_elements: bool = True,
) -> None:
    """Attach one URDF into another at a given parent link, in-place.

    All link and joint names in *attachment_dict* are prefixed with *child_prefix*
    to prevent name collisions. A single fixed joint is added connecting
    *parent_link* (in *base_dict*) to ``<child_prefix><child_root_link>``.

    Args:
        base_dict: Parsed URDF dictionary to attach into (modified in-place).
        attachment_dict: Parsed URDF dictionary of the component to attach
            (modified in-place – pass a copy if you need the original unchanged).
        parent_link: Name of the link in *base_dict* to attach to.
        child_prefix: Prefix applied to every link/joint name in the attachment,
            e.g. ``"schunk_"`` or ``"d435_"``.
        child_root_link: Name of the root link in the attachment URDF to connect
            to. Defaults to ``"base_link"``.
        attachment_urdf_path: If provided, mesh paths in *attachment_dict* are
            made absolute relative to this path before merging. Useful when the
            attachment URDF uses relative mesh paths and the merged file will be
            written elsewhere.
        origin_xyz: Translation of the attaching joint in metres, as an
            ``"x y z"`` string. Defaults to ``"0 0 0"``.
        origin_rpy: Rotation of the attaching joint in radians, as an
            ``"r p y"`` string. Defaults to ``"0 0 0"``.
        freeze_joints: If ``True`` (default), all non-fixed joints in
            *attachment_dict* are converted to fixed joints via
            :func:`make_static`. Set to ``False`` to keep the attachment's
            original joint types (e.g. for a gripper you want to control).
        copy_extra_elements: If ``True`` (default), robot-level elements other
            than ``link`` and ``joint`` (e.g. ``transmission``, ``gazebo``,
            ``mujoco``, robot-level ``material`` or ``drake:*`` tags) are also
            copied from the attachment into the base, with any link/joint name
            references updated to the prefixed names. Set to ``False`` to merge
            only links and joints.

    Example:
        Attach a Schunk gripper and a RealSense camera to an arm::

            arm = read_urdf("rm75_6f.urdf")
            gripper = read_urdf("schunk_egk40.urdf")
            camera = read_urdf("d435.urdf")

            attach_urdf(arm, gripper, "tool0", "schunk_",
                        attachment_urdf_path="schunk_egk40.urdf")
            attach_urdf(arm, camera, "tool0", "d435_",
                        attachment_urdf_path="d435.urdf",
                        origin_xyz="0 -0.06 -0.04")

            write_urdf_to_file(arm, "combined.urdf")
    """
    if attachment_urdf_path is not None:
        make_paths_absolute(attachment_dict, attachment_urdf_path)

    if freeze_joints:
        make_static(attachment_dict)

    # Map every original link/joint name to its prefixed version so that all
    # references (parent/child, mimic, transmission, drake members, ...) can be
    # updated consistently after prefixing the definitions.
    rename_map = {name: child_prefix + name for name in _collect_link_joint_names(attachment_dict)}

    _prefix_urdf_names(attachment_dict, child_prefix)
    # Fix any remaining name references that _prefix_urdf_names does not touch
    # (e.g. <mimic joint="...">). Already-prefixed names won't match rename_map.
    _rename_references(attachment_dict["robot"], rename_map)

    # Ensure base lists exist.
    _ensure_list(base_dict, "link")
    _ensure_list(base_dict, "joint")

    # Merge links and joints.
    att_robot = attachment_dict["robot"]
    att_links = att_robot.get("link", [])
    att_joints = att_robot.get("joint", [])
    if isinstance(att_links, dict):
        att_links = [att_links]
    if isinstance(att_joints, dict):
        att_joints = [att_joints]

    base_dict["robot"]["link"].extend(att_links)
    base_dict["robot"]["joint"].extend(att_joints)

    # Merge robot-level elements other than link/joint (transmission, gazebo,
    # mujoco, drake:* tags, robot-level materials, ...). References have already
    # been renamed above.
    if copy_extra_elements:
        for key, value in att_robot.items():
            if key.startswith("@") or key in ("link", "joint"):
                continue
            att_items = value if isinstance(value, list) else [value]
            if key not in base_dict["robot"]:
                base_dict["robot"][key] = list(att_items)
            else:
                if isinstance(base_dict["robot"][key], dict):
                    base_dict["robot"][key] = [base_dict["robot"][key]]
                base_dict["robot"][key].extend(att_items)

    # Add the fixed attaching joint.
    joint_name = f"{parent_link}_to_{child_prefix.rstrip('_')}"
    base_dict["robot"]["joint"].append(
        {
            "@name": joint_name,
            "@type": "fixed",
            "parent": {"@link": parent_link},
            "child": {"@link": f"{child_prefix}{child_root_link}"},
            "origin": {"@xyz": origin_xyz, "@rpy": origin_rpy},
        }
    )
