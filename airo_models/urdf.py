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
