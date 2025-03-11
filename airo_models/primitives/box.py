"""Python functions to easily generate parametrized URDF boxes."""

from airo_models.urdf import dict_to_xml_str, material_dict, single_link_urdf_dict, write_urdf_to_tempfile


def box_geometry_dict(size: tuple[float, float, float]) -> dict:
    geometry_dict = {"box": {"@size": " ".join(map(str, size))}}
    return geometry_dict


def box_dict(
    size: tuple[float, float, float], name: str = "box", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> dict:
    geometry_dict = box_geometry_dict(size)
    mat_dict = material_dict(rgba)
    box_dict_ = single_link_urdf_dict(name, geometry_dict, mat_dict)
    return box_dict_


def box_urdf(
    size: tuple[float, float, float], name: str = "box", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> str:
    box_dict_ = box_dict(size, name, rgba)
    urdf_str = dict_to_xml_str(box_dict_)
    return urdf_str


def box_urdf_path(
    size: tuple[float, float, float], name: str = "box", rgba: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
) -> str:
    urdf_path = write_urdf_to_tempfile(box_dict(size, name, rgba), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(box_urdf((0.5, 1.0, 2.0)))
