"""Clean the meshes referenced by an airo-models URDF using trimesh.

Meshes exported from CAD/DCC tools (and many ``.obj`` files in particular) often
carry defects that are harmless for rendering but problematic for downstream
geometry processing (convex decomposition, collision checking, remeshing):

* **duplicated vertices** -- unindexed meshes store one vertex per triangle
  corner, so a mesh can have several times more vertices than needed;
* **duplicated faces** -- the exact same triangle appearing more than once;
* **degenerate faces** -- zero-area triangles (collinear / coincident corners);
* **unreferenced (isolated) vertices** -- vertices not used by any face.

This is the ``trimesh`` equivalent of PyMesh's *Local Mesh Cleanup Tools*:

===============================  =====================================================
PyMesh                           trimesh
===============================  =====================================================
``remove_duplicated_vertices``   ``Trimesh.merge_vertices()``
``remove_duplicated_faces``      ``Trimesh.update_faces(Trimesh.unique_faces())``
``remove_degenerated_triangles`` ``Trimesh.update_faces(Trimesh.nondegenerate_faces())``
``remove_isolated_vertices``     ``Trimesh.remove_unreferenced_vertices()``
===============================  =====================================================

By default every mesh referenced by a ``<visual>`` or ``<collision>`` element of
the URDF is cleaned **in place** (the repository is version controlled, so use
``git diff`` / ``git checkout`` to inspect or revert). Use ``--check`` to only
print a diagnostic report without modifying any files.

Run with a known model name (see ``AIRO_MODEL_NAMES``) or a path to any URDF::

    python scripts/clean_meshes.py rm75_6f            # clean in place
    python scripts/clean_meshes.py rm75_6f --check    # report only
    python scripts/clean_meshes.py path/to/robot.urdf

Requires the optional collision dependencies (for ``trimesh``)::

    pip install airo-models[collision]
"""

import argparse
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


def collect_mesh_paths(urdf_path: str) -> list[str]:
    """Return the absolute paths of all (unique) meshes referenced by the URDF.

    Both ``<visual>`` and ``<collision>`` geometries are included; ``@filename``
    attributes are found by recursively walking the parsed URDF dictionary so we
    don't depend on the exact link/visual/collision nesting.
    """
    urdf_dict = urdf_utils.read_urdf(urdf_path)

    filenames: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "@filename" and isinstance(value, str):
                    filenames.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(urdf_dict)

    seen: set[str] = set()
    mesh_paths: list[str] = []
    for filename in filenames:
        abs_path = urdf_utils.make_path_absolute(filename, urdf_path)
        if abs_path.lower().endswith((".obj", ".stl", ".ply", ".dae")) and abs_path not in seen:
            seen.add(abs_path)
            mesh_paths.append(abs_path)
    return mesh_paths


def mesh_defects(mesh: trimesh.Trimesh) -> dict:
    """Count the local defects of a mesh (see module docstring for the categories)."""
    num_vertices, num_faces = len(mesh.vertices), len(mesh.faces)

    merged = mesh.copy()
    merged.merge_vertices()

    referenced = np.zeros(num_vertices, dtype=bool)
    referenced[mesh.faces.reshape(-1)] = True

    return {
        "vertices": num_vertices,
        "faces": num_faces,
        "duplicated_vertices": int(num_vertices - len(merged.vertices)),
        "duplicated_faces": int(num_faces - int(mesh.unique_faces().sum())),
        "degenerate_faces": int(num_faces - int(mesh.nondegenerate_faces().sum())),
        "isolated_vertices": int((~referenced).sum()),
    }


def clean_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Apply the local cleanup operations (in place) and return the mesh.

    Order matters: remove duplicated/degenerate faces first, then merge
    coincident vertices and finally drop any vertices left unreferenced.
    """
    mesh.update_faces(mesh.unique_faces())
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    return mesh


def defects_summary(defects: dict) -> str:
    """Render the non-zero defect counts of a mesh as a compact string."""
    flags = [
        f"{key}={defects[key]}"
        for key in ("duplicated_vertices", "duplicated_faces", "degenerate_faces", "isolated_vertices")
        if defects[key] > 0
    ]
    return ", ".join(flags) if flags else "clean"


def process_urdf_meshes(urdf_path: str, check_only: bool) -> None:
    """Report (and optionally fix) the local defects of every mesh in the URDF."""
    mesh_paths = collect_mesh_paths(urdf_path)
    urdf_dir = os.path.dirname(os.path.abspath(urdf_path))

    print(f"URDF:   {urdf_path}")
    print(f"Meshes: {len(mesh_paths)}")
    print(f"Mode:   {'check only (no files modified)' if check_only else 'cleaning in place'}\n")

    num_defective = 0
    for mesh_path in mesh_paths:
        # process=False keeps the mesh exactly as stored so we measure the real defects.
        mesh = trimesh.load(mesh_path, force="mesh", process=False)
        rel = os.path.relpath(mesh_path, urdf_dir)

        before = mesh_defects(mesh)
        has_defects = defects_summary(before) != "clean"
        if has_defects:
            num_defective += 1

        if check_only:
            print(f"  {rel:48s} V={before['vertices']:7d} F={before['faces']:7d}  {defects_summary(before)}")
            continue

        if not has_defects:
            print(f"  {rel:48s} clean, skipped")
            continue

        clean_mesh(mesh)
        mesh.export(mesh_path)
        after = mesh_defects(mesh)
        print(
            f"  {rel:48s} V={before['vertices']:7d}->{after['vertices']:<7d} "
            f"F={before['faces']:7d}->{after['faces']:<7d}  fixed [{defects_summary(before)}]"
        )

    verb = "have" if num_defective != 1 else "has"
    print(f"\nDone. {num_defective}/{len(mesh_paths)} meshes {verb} defects" + ("." if check_only else " (cleaned)."))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", help="A known model name (e.g. 'rm75_6f') or a path to a URDF file.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report mesh defects; do not modify any files.",
    )
    args = parser.parse_args()

    urdf_path = resolve_urdf_path(args.model)
    process_urdf_meshes(urdf_path, check_only=args.check)


if __name__ == "__main__":
    main()
