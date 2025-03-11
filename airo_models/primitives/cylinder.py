"""Python functions to easily generate parametrized URDF cylinders."""

from airo_models.urdf import dict_to_xml_str, material_dict, single_link_urdf_dict, write_urdf_to_tempfile


def cylinder_geometry_dict(length: float, radius: float) -> dict:
    geometry_dict = {"cylinder": {"@length": str(length), "@radius": str(radius)}}
    return geometry_dict


def cylinder_dict(
    length: float,
    radius: float,
    name: str = "cylinder",
    rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
) -> dict:
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
    cylinder_dict_ = cylinder_dict(length, radius, name, rgba)
    urdf_str = dict_to_xml_str(cylinder_dict_)
    return urdf_str


def cylinder_urdf_path(
    length: float,
    radius: float,
    name: str = "cylinder",
    rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
) -> str:
    urdf_path = write_urdf_to_tempfile(cylinder_dict(length, radius, name, rgba), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(cylinder_urdf(2.0, 0.5))
