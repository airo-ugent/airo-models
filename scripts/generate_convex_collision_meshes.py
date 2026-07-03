"""Generate convex collision meshes for an airo-models URDF using CoACD.

Motion planners typically require *convex* collision geometry and perform many
collision/distance queries, so the raw (often concave, high-triangle) visual
meshes used as collision geometry are both incompatible and slow. This script
runs `CoACD <https://github.com/SarahWeiii/CoACD>`_ (Approximate Convex
Decomposition) on every mesh referenced by a ``<collision>`` element and writes
a new URDF in which each such collision mesh is replaced by a set of convex
``.obj`` parts.

Visual geometry, inertial data, joints and any non-mesh collision primitives are
copied over unchanged.

Run with a known model name (see ``AIRO_MODEL_NAMES``) or a path to any URDF::

    python scripts/generate_convex_collision_meshes.py rm75_6f
    python scripts/generate_convex_collision_meshes.py path/to/robot.urdf --threshold 0.03

By default, for a model located at ``<dir>/<name>.urdf`` the convex parts are
written to ``<dir>/collision_convex/`` and the new URDF to
``<dir>/<name>_convex_collision.urdf``.

Requires the optional collision dependencies::

    pip install airo-models[collision]
"""

import argparse
import copy
import os
import sys
from pathlib import Path

import coacd
import numpy as np
import trimesh

# Allow running from a git clone without having installed the package: make the
# repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import airo_models  # noqa: E402
from airo_models import urdf as urdf_utils  # noqa: E402


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


def decompose_mesh(mesh_path: str, threshold: float, preprocess_resolution: int, seed: int) -> list[trimesh.Trimesh]:
    """Run CoACD on a single mesh file and return the resulting convex parts as trimesh meshes."""
    mesh = trimesh.load(mesh_path, force="mesh")
    assert isinstance(mesh, trimesh.Trimesh), f"Expected a single mesh from {mesh_path}, got {type(mesh)}"
    coacd_mesh = coacd.Mesh(np.asarray(mesh.vertices), np.asarray(mesh.faces))
    parts = coacd.run_coacd(
        coacd_mesh,
        threshold=threshold,
        preprocess_resolution=preprocess_resolution,
        seed=seed,
    )
    return [trimesh.Trimesh(vertices=vertices, faces=faces) for vertices, faces in parts]


def convex_collision_elements(
    collision: dict,
    link_name: str,
    collision_index: int,
    input_urdf_path: str,
    output_mesh_dir: str,
    output_urdf_dir: str,
    threshold: float,
    preprocess_resolution: int,
    seed: int,
) -> list[dict]:
    """Convert a single ``<collision>`` element into one or more convex-part collision elements.

    Non-mesh geometries (box, cylinder, sphere) are returned unchanged. For mesh geometries the
    referenced mesh is decomposed with CoACD and one collision element is emitted per convex part,
    each keeping the original ``<origin>``.
    """
    geometry = collision.get("geometry", {})
    if "mesh" not in geometry:
        return [collision]

    mesh_rel_path = geometry["mesh"]["@filename"]
    mesh_abs_path = urdf_utils.make_path_absolute(mesh_rel_path, input_urdf_path)

    convex_parts = decompose_mesh(mesh_abs_path, threshold, preprocess_resolution, seed)

    mesh_stem = Path(mesh_rel_path).stem
    origin = collision.get("origin")

    collision_elements: list[dict] = []
    for part_index, part in enumerate(convex_parts):
        part_filename = f"{link_name}_collision_{collision_index}_part_{part_index}.obj"
        part.export(os.path.join(output_mesh_dir, part_filename))

        rel_filename = os.path.relpath(os.path.join(output_mesh_dir, part_filename), output_urdf_dir)
        element: dict = {"geometry": {"mesh": {"@filename": rel_filename}}}
        if origin is not None:
            element["origin"] = copy.deepcopy(origin)
        collision_elements.append(element)

    print(f"  {link_name} (collision {collision_index}): {mesh_stem} -> {len(convex_parts)} convex parts")
    return collision_elements


def generate_convex_collision_urdf(
    input_urdf_path: str,
    output_urdf_path: str,
    output_mesh_dir: str,
    threshold: float,
    preprocess_resolution: int,
    seed: int,
) -> None:
    """Read a URDF, replace every mesh collision by its CoACD convex decomposition, and write a new URDF."""
    os.makedirs(output_mesh_dir, exist_ok=True)
    output_urdf_dir = os.path.dirname(os.path.abspath(output_urdf_path))

    urdf_dict = urdf_utils.read_urdf(input_urdf_path)

    for link in as_list(urdf_dict["robot"]["link"]):
        collisions = as_list(link.get("collision"))
        if not collisions:
            continue

        new_collisions: list[dict] = []
        for collision_index, collision in enumerate(collisions):
            new_collisions.extend(
                convex_collision_elements(
                    collision,
                    link["@name"],
                    collision_index,
                    input_urdf_path,
                    output_mesh_dir,
                    output_urdf_dir,
                    threshold,
                    preprocess_resolution,
                    seed,
                )
            )

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
        help="Path for the generated URDF (default: '<input>_convex_collision.urdf' next to the input).",
    )
    parser.add_argument(
        "--output-mesh-dir",
        default=None,
        help="Directory for the convex mesh parts (default: 'collision_convex/' next to the input URDF).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="CoACD concavity threshold in [0.01, 1]; lower = more parts / higher accuracy (default: 0.05).",
    )
    parser.add_argument(
        "--preprocess-resolution",
        type=int,
        default=50,
        help="CoACD manifold preprocessing resolution; higher = finer but slower (default: 50).",
    )
    parser.add_argument("--seed", type=int, default=0, help="CoACD random seed for reproducibility (default: 0).")
    args = parser.parse_args()

    input_urdf_path = resolve_urdf_path(args.model)
    input_dir = os.path.dirname(input_urdf_path)
    input_stem = Path(input_urdf_path).stem

    output_urdf_path = args.output_urdf or os.path.join(input_dir, f"{input_stem}_convex_collision.urdf")
    output_mesh_dir = args.output_mesh_dir or os.path.join(input_dir, "collision_convex")

    coacd.set_log_level("error")

    print(f"Input URDF:   {input_urdf_path}")
    print(f"Output URDF:  {output_urdf_path}")
    print(f"Mesh parts:   {output_mesh_dir}")
    print(f"CoACD threshold={args.threshold}, preprocess_resolution={args.preprocess_resolution}, seed={args.seed}")

    generate_convex_collision_urdf(
        input_urdf_path,
        output_urdf_path,
        output_mesh_dir,
        args.threshold,
        args.preprocess_resolution,
        args.seed,
    )
    print("Done.")


if __name__ == "__main__":
    main()
