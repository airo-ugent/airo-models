"""Python functions to easily generate parametrized URDF cylinders.

A cylinder is defined by its length (height) and radius. The origin is at the geometric center,
with the axis of the cylinder aligned with the Z direction.
"""

from airo_models.urdf import dict_to_xml_str, material_dict, single_link_urdf_dict, write_urdf_to_tempfile


def cylinder_geometry_dict(length: float, radius: float) -> dict:
    """Create a URDF cylinder geometry element as a dictionary.

    Args:
        length: The height of the cylinder in meters (extent along the Z-axis).
        radius: The radius of the cylinder in meters.

    Returns:
        A dictionary representation of a URDF cylinder geometry element.

    Example:
        >>> geom = cylinder_geometry_dict(2.0, 0.5)
        >>> geom  # doctest: +SKIP
        {'cylinder': {'@length': '2.0', '@radius': '0.5'}}
    """
    geometry_dict = {"cylinder": {"@length": str(length), "@radius": str(radius)}}
    return geometry_dict


def cylinder_dict(
    length: float,
    radius: float,
    name: str = "cylinder",
    rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
) -> dict:
    """Create a complete single-link URDF cylinder model as a dictionary.

    Args:
        length: The height of the cylinder in meters (extent along the Z-axis).
        radius: The radius of the cylinder in meters.
        name: Name of the URDF model and link. Defaults to "cylinder".
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A dictionary representation of a complete single-link URDF model with a cylinder geometry.

    Example:
        >>> cyl = cylinder_dict(1.0, 0.05, name="rod", rgba=(0.5, 0.5, 0.5, 1.0))
    """
    geometry_dict = cylinder_geometry_dict(length, radius)
    mat_dict = material_dict(rgba)
    cylinder_dict_ = single_link_urdf_dict(name, geometry_dict, mat_dict)
    return cylinder_dict_


def cylinder_urdf(
    length: float,
    radius: float,
    name: str = "cylinder",
    rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
) -> str:
    """Generate a URDF string for a cylinder.

    Args:
        length: The height of the cylinder in meters (extent along the Z-axis).
        radius: The radius of the cylinder in meters.
        name: Name of the URDF model and link. Defaults to "cylinder".
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A string containing the URDF in XML format.

    Example:
        >>> urdf_str = cylinder_urdf(2.0, 0.5)
        >>> print(urdf_str)  # doctest: +SKIP
    """
    cylinder_dict_ = cylinder_dict(length, radius, name, rgba)
    urdf_str = dict_to_xml_str(cylinder_dict_)
    return urdf_str


def cylinder_urdf_path(
    length: float,
    radius: float,
    name: str = "cylinder",
    rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
) -> str:
    """Generate a URDF file for a cylinder and return the path to a temporary file.

    The temporary file is created with a prefix based on the model name. It will be cleaned up by
    the operating system when the program exits (or can be deleted manually).

    Args:
        length: The height of the cylinder in meters (extent along the Z-axis).
        radius: The radius of the cylinder in meters.
        name: Name of the URDF model and link. Defaults to "cylinder". Also used as the prefix for the temp file.
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A string path to a temporary URDF file.

    Example:
        >>> path = cylinder_urdf_path(1.0, 0.05, name="rod")
        >>> print(path)  # doctest: +SKIP
        /tmp/rod_xyz.urdf
    """
    urdf_path = write_urdf_to_tempfile(cylinder_dict(length, radius, name, rgba), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(cylinder_urdf(2.0, 0.5))
