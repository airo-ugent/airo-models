"""Python functions to easily generate a single-link URDF from a mesh file.

This module allows you to wrap an existing mesh file (e.g., .obj, .stl, .dae) in a URDF model.
The origin of the generated URDF is at (0, 0, 0) with no rotation.
"""

from airo_models.urdf import dict_to_xml_str, material_dict, single_link_urdf_dict, write_urdf_to_tempfile


def mesh_geometry_dict(mesh_file: str) -> dict:
    """Create a URDF mesh geometry element as a dictionary.

    Args:
        mesh_file: Path to the mesh file (e.g., "/path/to/mesh.obj" or "file:///path/to/mesh.stl").
                   Supports .obj, .stl, .dae, and other formats supported by URDF and your simulator.

    Returns:
        A dictionary representation of a URDF mesh geometry element.

    Example:
        >>> geom = mesh_geometry_dict("/path/to/model.obj")
        >>> geom  # doctest: +SKIP
        {'mesh': {'@filename': '/path/to/model.obj'}}
    """
    geometry_dict = {"mesh": {"@filename": mesh_file}}
    return geometry_dict


def mesh_dict(mesh_file: str, name: str = "mesh") -> dict:
    """Create a complete single-link URDF mesh model as a dictionary.

    Args:
        mesh_file: Path to the mesh file (e.g., "/path/to/mesh.obj" or "file:///path/to/mesh.stl").
                   Supports .obj, .stl, .dae, and other formats supported by URDF and your simulator.
        name: Name of the URDF model and link. Defaults to "mesh".

    Returns:
        A dictionary representation of a complete single-link URDF model with a mesh geometry.

    Example:
        >>> mesh = mesh_dict("/path/to/custom_object.obj", name="object")
    """
    geometry_dict = mesh_geometry_dict(mesh_file)
    mat_dict = material_dict((1.0, 1.0, 1.0, 1.0))
    mesh_dict_ = single_link_urdf_dict(name, geometry_dict, mat_dict)
    return mesh_dict_


def mesh_urdf(mesh_file: str, name: str = "mesh") -> str:
    """Generate a URDF string for a mesh.

    Args:
        mesh_file: Path to the mesh file (e.g., "/path/to/mesh.obj" or "file:///path/to/mesh.stl").
                   Supports .obj, .stl, .dae, and other formats supported by URDF and your simulator.
        name: Name of the URDF model and link. Defaults to "mesh".

    Returns:
        A string containing the URDF in XML format.

    Example:
        >>> urdf_str = mesh_urdf("/path/to/model.obj")
        >>> print(urdf_str)  # doctest: +SKIP
    """
    mesh_dict_ = mesh_dict(mesh_file, name)
    urdf_str = dict_to_xml_str(mesh_dict_)
    return urdf_str


def mesh_urdf_path(mesh_file: str, name: str = "mesh") -> str:
    """Generate a URDF file for a mesh and return the path to a temporary file.

    The temporary file is created with a prefix based on the model name. It will be cleaned up by
    the operating system when the program exits (or can be deleted manually).

    Args:
        mesh_file: Path to the mesh file (e.g., "/path/to/mesh.obj" or "file:///path/to/mesh.stl").
                   Supports .obj, .stl, .dae, and other formats supported by URDF and your simulator.
        name: Name of the URDF model and link. Defaults to "mesh". Also used as the prefix for the temp file.

    Returns:
        A string path to a temporary URDF file.

    Example:
        >>> path = mesh_urdf_path("/path/to/model.obj", name="object")
        >>> print(path)  # doctest: +SKIP
        /tmp/object_xyz.urdf
    """
    urdf_path = write_urdf_to_tempfile(mesh_dict(mesh_file, name), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(mesh_urdf("/path/to/your/mesh.obj"))
