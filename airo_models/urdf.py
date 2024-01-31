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
    return xmltodict.unparse(dict_, pretty=True, indent="  ")


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


def make_paths_absolute(dict_: dict, urdf_path: str) -> None:
    for key, value in dict_.items():
        if key == "@filename" and not os.path.isabs(value):
            dict_[key] = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(urdf_path)), value))
        # Recurse
        elif isinstance(value, dict):
            make_paths_absolute(value, urdf_path)
        elif isinstance(value, list):
            for item in value:
                make_paths_absolute(item, urdf_path)
