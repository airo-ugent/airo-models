"""Python functions to easily generate parametrized URDF spheres.

A sphere is defined by its radius. The origin is at the geometric center of the sphere.
"""

from airo_models.urdf import dict_to_xml_str, material_dict, single_link_urdf_dict, write_urdf_to_tempfile


def sphere_geometry_dict(radius: float) -> dict:
    """Create a URDF sphere geometry element as a dictionary.

    Args:
        radius: The radius of the sphere in meters.

    Returns:
        A dictionary representation of a URDF sphere geometry element.

    Example:
        >>> geom = sphere_geometry_dict(0.5)
        >>> geom  # doctest: +SKIP
        {'sphere': {'@radius': '0.5'}}
    """
    geometry_dict = {"sphere": {"@radius": str(radius)}}
    return geometry_dict


def sphere_dict(
    radius: float, name: str = "sphere", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> dict:
    """Create a complete single-link URDF sphere model as a dictionary.

    Args:
        radius: The radius of the sphere in meters.
        name: Name of the URDF model and link. Defaults to "sphere".
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A dictionary representation of a complete single-link URDF model with a sphere geometry.

    Example:
        >>> sphere = sphere_dict(0.1, name="ball", rgba=(1.0, 1.0, 0.0, 1.0))
    """
    geometry_dict = sphere_geometry_dict(radius)
    mat_dict = material_dict(rgba)
    sphere_dict_ = single_link_urdf_dict(name, geometry_dict, mat_dict)
    return sphere_dict_


def sphere_urdf(
    radius: float, name: str = "sphere", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> str:
    """Generate a URDF string for a sphere.

    Args:
        radius: The radius of the sphere in meters.
        name: Name of the URDF model and link. Defaults to "sphere".
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A string containing the URDF in XML format.

    Example:
        >>> urdf_str = sphere_urdf(0.5)
        >>> print(urdf_str)  # doctest: +SKIP
    """
    sphere_dict_ = sphere_dict(radius, name, rgba)
    urdf_str = dict_to_xml_str(sphere_dict_)
    return urdf_str


def sphere_urdf_path(
    radius: float, name: str = "sphere", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> str:
    """Generate a URDF file for a sphere and return the path to a temporary file.

    The temporary file is created with a prefix based on the model name. It will be cleaned up by
    the operating system when the program exits (or can be deleted manually).

    Args:
        radius: The radius of the sphere in meters.
        name: Name of the URDF model and link. Defaults to "sphere". Also used as the prefix for the temp file.
        rgba: A tuple of (red, green, blue, alpha) color values in the range [0, 1].
              Defaults to white with full opacity (1.0, 1.0, 1.0, 1.0).

    Returns:
        A string path to a temporary URDF file.

    Example:
        >>> path = sphere_urdf_path(0.1, name="ball")
        >>> print(path)  # doctest: +SKIP
        /tmp/ball_xyz.urdf
    """
    urdf_path = write_urdf_to_tempfile(sphere_dict(radius, name, rgba), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(sphere_urdf(0.5))
