"""Python functions to easily generate parametrized URDF boxes."""

from airo_models.urdf import dict_to_xml_str, single_link_urdf_dict, write_urdf_to_tempfile


def box_geometry_dict(size: tuple[float, float, float]) -> dict:
    geometry_dict = {"box": {"@size": " ".join(map(str, size))}}
    return geometry_dict


def box_dict(size: tuple[float, float, float], name: str = "box") -> dict:
    geometry_dict = box_geometry_dict(size)
    box_dict_ = single_link_urdf_dict(name, geometry_dict)
    return box_dict_


def box_urdf(size: tuple[float, float, float], name: str = "box") -> str:
    box_dict_ = box_dict(size, name)
    urdf_str = dict_to_xml_str(box_dict_)
    return urdf_str


def box_urdf_path(size: tuple[float, float, float], name: str = "box") -> str:
    urdf_path = write_urdf_to_tempfile(box_dict(size, name), prefix=f"{name}_")
    return urdf_path


if __name__ == "__main__":
    print(box_urdf((0.5, 1.0, 2.0)))
