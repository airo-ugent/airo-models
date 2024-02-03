"""Python functions to easily generate parametrized URDF spheres."""

from airo_models.urdf import dict_to_xml_str, single_link_urdf_dict, write_urdf_to_tempfile


def sphere_geometry_dict(radius: float) -> dict:
    geometry_dict = {"sphere": {"@radius": str(radius)}}
    return geometry_dict


def sphere_dict(radius: float, name: str = "sphere") -> dict:
    geometry_dict = sphere_geometry_dict(radius)
    sphere_dict_ = single_link_urdf_dict(name, geometry_dict)
    return sphere_dict_


def sphere_urdf(radius: float, name: str = "sphere") -> str:
    sphere_dict_ = sphere_dict(radius, name)
    urdf_str = dict_to_xml_str(sphere_dict_)
    return urdf_str


def sphere_urdf_path(radius: float, name: str = "sphere") -> str:
    urdf_path = write_urdf_to_tempfile(sphere_dict(radius, name), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(sphere_urdf(0.5))
