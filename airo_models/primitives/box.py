"""Python functions to easily generate parametrized URDF boxes.

A box is a rectangular cuboid defined by its extents in the X, Y, and Z directions.
The origin is at the geometric center of the box.
"""

from airo_models.urdf import dict_to_xml_str, material_dict, single_link_urdf_dict, write_urdf_to_tempfile


def box_geometry_dict(size: tuple[float, float, float]) -> dict:
    """Create a URDF box geometry element as a dictionary.

    Args:
        size: A tuple of (length_x, length_y, length_z) representing the extents of the box in meters.

    Returns:
        A dictionary representation of a URDF box geometry element.

    Example:
        >>> geom = box_geometry_dict((0.5, 1.0, 2.0))
        >>> geom  # doctest: +SKIP
        {'box': {'@size': '0.5 1.0 2.0'}}
    """
    geometry_dict = {"box": {"@size": " ".join(map(str, size))}}
    return geometry_dict


def box_dict(
    size: tuple[float, float, float], name: str = "box", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> dict:
    """Create a complete single-link URDF box model as a dictionary.

    Args:
        size: A tuple of (length_x, length_y, length_z) representing the extents of the box in meters.
        name: Name of the URDF model and link. Defaults to "box".
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A dictionary representation of a complete single-link URDF model with a box geometry.

    Example:
        >>> box = box_dict((0.5, 1.0, 2.0), name="my_box", rgba=(1.0, 0.0, 0.0, 1.0))
    """
    geometry_dict = box_geometry_dict(size)
    mat_dict = material_dict(rgba)
    box_dict_ = single_link_urdf_dict(name, geometry_dict, mat_dict)
    return box_dict_


def box_urdf(
    size: tuple[float, float, float], name: str = "box", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> str:
    """Generate a URDF string for a box.

    Args:
        size: A tuple of (length_x, length_y, length_z) representing the extents of the box in meters.
        name: Name of the URDF model and link. Defaults to "box".
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A string containing the URDF in XML format.

    Example:
        >>> urdf_str = box_urdf((0.5, 1.0, 2.0))
        >>> print(urdf_str)  # doctest: +SKIP
    """
    box_dict_ = box_dict(size, name, rgba)
    urdf_str = dict_to_xml_str(box_dict_)
    return urdf_str


def box_urdf_path(
    size: tuple[float, float, float], name: str = "box", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> str:
    """Generate a URDF file for a box and return the path to a temporary file.

    The temporary file is created with a prefix based on the model name. It will be cleaned up by
    the operating system when the program exits (or can be deleted manually).

    Args:
        size: A tuple of (length_x, length_y, length_z) representing the extents of the box in meters.
        name: Name of the URDF model and link. Defaults to "box". Also used as the prefix for the temp file.
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A string path to a temporary URDF file.

    Example:
        >>> path = box_urdf_path((0.5, 1.0, 2.0), name="my_box")
        >>> print(path)  # doctest: +SKIP
        /tmp/my_box_xyz.urdf
    """
    urdf_path = write_urdf_to_tempfile(box_dict(size, name, rgba), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(box_urdf((0.5, 1.0, 2.0)))
