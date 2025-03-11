"""Python functions to easily generate a single-link URDF from a mesh file."""

from airo_models.urdf import dict_to_xml_str, material_dict, single_link_urdf_dict, write_urdf_to_tempfile


def mesh_geometry_dict(mesh_file: str) -> dict:
    geometry_dict = {"mesh": {"@filename": mesh_file}}
    return geometry_dict


def mesh_dict(mesh_file: str, name: str = "mesh") -> dict:
    geometry_dict = mesh_geometry_dict(mesh_file)
    mat_dict = material_dict((1.0, 1.0, 1.0, 1.0))
    mesh_dict_ = single_link_urdf_dict(name, geometry_dict, mat_dict)
    return mesh_dict_


def mesh_urdf(mesh_file: str, name: str = "mesh") -> str:
    mesh_dict_ = mesh_dict(mesh_file, name)
    urdf_str = dict_to_xml_str(mesh_dict_)
    return urdf_str


def mesh_urdf_path(mesh_file: str, name: str = "mesh") -> str:
    urdf_path = write_urdf_to_tempfile(mesh_dict(mesh_file, name), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(mesh_urdf("/path/to/your/mesh.obj"))
