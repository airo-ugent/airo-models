"""Generate a primitive (cylinder) collision model for an airo-models URDF.

Motion planners perform many collision/distance queries, and closed-form
primitive checks (sphere/cylinder) are roughly an order of magnitude cheaper
than convex-mesh queries. This script approximates every mesh referenced by a
link's ``<visual>`` element with a single bounding **cylinder** and writes a new
URDF using those primitives as ``<collision>`` geometry.

For each such link the mesh is loaded in its own link frame and its
axis-aligned bounding box is computed. The cylinder is aligned with one local
axis (``x``, ``y`` or ``z``); by default the longest extent is chosen
automatically, but this can be overridden per link with ``--axis-map``. The
cylinder length equals the extent along that axis and its radius equals half of
the larger of the two remaining extents, so the cylinder fully encloses the
bounding box cross-section (a conservative, watertight fit).

Visual geometry, inertial data and joints are copied over unchanged.

Run with a known model name (see ``AIRO_MODEL_NAMES``) or a path to a URDF::

    python scripts/generate_primitive_collision_meshes.py rm75_6f \
        --axis-map link_2:y,link_4:y,link_6:y,link_7:z

By default, for a model at ``<dir>/<name>.urdf`` the new URDF is written to
``<dir>/<name>_primitives.urdf``.

Requires the optional collision dependencies::

    pip install airo-models[collision]
"""

import argparse
import copy
import os
import sys
from pathlib import Path

import numpy as np
import trimesh

# Allow running from a git clone without having installed the package: make the
# repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import airo_models  # noqa: E402
from airo_models import urdf as urdf_utils  # noqa: E402

# rpy (roll-pitch-yaw) that rotates the cylinder's local +Z axis onto the chosen link axis.
AXIS_TO_RPY = {
    "x": "0 1.5707963267948966 0",
    "y": "-1.5707963267948966 0 0",
    "z": "0 0 0",
}
AXIS_TO_INDEX = {"x": 0, "y": 1, "z": 2}


def resolve_urdf_path(name_or_path: str) -> str:
    """Resolve a model name from AIRO_MODEL_NAMES or an existing URDF path."""
    if os.path.isfile(name_or_path):
        return os.path.abspath(name_or_path)
    try:
        return airo_models.get_urdf_path(name_or_path)
    except ValueError as e:
        raise ValueError(
            f"'{name_or_path}' is not an existing file nor a known model. "
            f"Known models: {airo_models.AIRO_MODEL_NAMES}"
        ) from e


def as_list(value: object) -> list:
    """xmltodict represents a single child as a dict and multiple as a list; normalise to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_axis_map(axis_map_str: str | None) -> dict[str, str]:
    """Parse a 'link_a:y,link_b:z' style string into a {link_name: axis} mapping."""
    if not axis_map_str:
        return {}
    axis_map: dict[str, str] = {}
    for item in axis_map_str.split(","):
        link_name, _, axis = item.partition(":")
        axis = axis.strip().lower()
        if axis not in AXIS_TO_RPY:
            raise ValueError(f"Invalid axis '{axis}' for link '{link_name}'; expected one of x, y, z.")
        axis_map[link_name.strip()] = axis
    return axis_map


def fit_cylinder(mesh_path: str, axis: str | None) -> tuple[str, np.ndarray, float, float]:
    """Fit a bounding cylinder to a mesh in its own (link) frame.

    Returns the chosen axis, the bounding-box center, the cylinder length (extent along the axis)
    and the cylinder radius (half of the larger remaining extent).
    """
    mesh = trimesh.load(mesh_path, force="mesh")
    assert isinstance(mesh, trimesh.Trimesh), f"Expected a single mesh from {mesh_path}, got {type(mesh)}"
    lower, upper = mesh.bounds
    extents = upper - lower
    center = (lower + upper) / 2.0

    if axis is None:
        axis = "xyz"[int(np.argmax(extents))]

    axis_index = AXIS_TO_INDEX[axis]
    length = float(extents[axis_index])
    radius = float(max(extents[i] for i in range(3) if i != axis_index) / 2.0)
    return axis, center, length, radius


def primitive_collision_element(source: dict, link_name: str, input_urdf_path: str, axis: str | None) -> dict:
    """Convert a single mesh source (``<visual>``) element into a bounding-cylinder collision element.

    Non-mesh geometries (box, cylinder, sphere) are returned unchanged.
    """
    geometry = source.get("geometry", {})
    if "mesh" not in geometry:
        return source

    mesh_rel_path = geometry["mesh"]["@filename"]
    mesh_abs_path = urdf_utils.make_path_absolute(mesh_rel_path, input_urdf_path)

    chosen_axis, center, length, radius = fit_cylinder(mesh_abs_path, axis)

    # Compose the link's own visual origin (if any) with the cylinder-in-link-frame pose.
    base_origin = source.get("origin", {})
    base_xyz = np.array([float(v) for v in base_origin.get("@xyz", "0 0 0").split()])

    element = {
        "origin": {
            "@xyz": " ".join(str(v) for v in (base_xyz + center)),
            "@rpy": AXIS_TO_RPY[chosen_axis],
        },
        "geometry": {"cylinder": {"@length": str(length), "@radius": str(radius)}},
    }
    print(f"  {link_name}: axis={chosen_axis} length={length:.4f} radius={radius:.4f}")
    return element


def generate_primitive_collision_urdf(
    input_urdf_path: str,
    output_urdf_path: str,
    axis_map: dict[str, str],
) -> None:
    """Read a URDF and build a bounding-cylinder collision model from each link's visual mesh."""
    urdf_dict = urdf_utils.read_urdf(input_urdf_path)

    for link in as_list(urdf_dict["robot"]["link"]):
        visuals = as_list(link.get("visual"))
        if not visuals:
            continue

        axis = axis_map.get(link["@name"])
        new_collisions = [
            primitive_collision_element(copy.deepcopy(source), link["@name"], input_urdf_path, axis)
            for source in visuals
        ]
        # xmltodict serialises a single-element list and a dict differently; use a dict when there is
        # exactly one collision element so the output matches hand-written URDFs.
        link["collision"] = new_collisions if len(new_collisions) > 1 else new_collisions[0]

    urdf_utils.write_urdf_to_file(urdf_dict, output_urdf_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", help="A known model name (e.g. 'rm75_6f') or a path to a URDF file.")
    parser.add_argument(
        "--output-urdf",
        default=None,
        help="Path for the generated URDF (default: '<input>_primitives.urdf' next to the input).",
    )
    parser.add_argument(
        "--axis-map",
        default=None,
        help="Comma-separated 'link:axis' overrides, e.g. 'link_2:y,link_7:z'. Links not listed use "
        "their longest bounding-box extent as the cylinder axis.",
    )
    args = parser.parse_args()

    input_urdf_path = resolve_urdf_path(args.model)
    input_dir = os.path.dirname(input_urdf_path)
    input_stem = Path(input_urdf_path).stem

    output_urdf_path = args.output_urdf or os.path.join(input_dir, f"{input_stem}_primitives.urdf")
    axis_map = parse_axis_map(args.axis_map)

    print(f"Input URDF:  {input_urdf_path}")
    print(f"Output URDF: {output_urdf_path}")
    if axis_map:
        print(f"Axis overrides: {axis_map}")

    generate_primitive_collision_urdf(input_urdf_path, output_urdf_path, axis_map)
    print("Done.")


if __name__ == "__main__":
    main()
