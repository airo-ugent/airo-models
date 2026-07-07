"""Render a preview image for every registered airo-models URDF.

Saves one PNG per model to an output directory (default: ``docs/images/``
relative to the repo root).  Run from the repo root:

    python scripts/render_model_images.py

Optional arguments:

    --output-dir PATH    Directory to write images to (default: docs/images)
    --size N             Square image resolution in pixels (default: 400)
    --models A B ...     Render only the listed model names

Requires the ``render`` optional dependencies:

    pip install airo-models[render]
"""

import argparse
import os
from pathlib import Path

import numpy as np

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import airo_models


def _bake_color(mesh: "trimesh.Trimesh") -> "trimesh.Trimesh":  # type: ignore[name-defined]
    """Return a copy of *mesh* with the diffuse/PBR base color baked into vertex colors.

    pyrender's MetallicRoughnessMaterial internally creates OpenGL textures even for
    solid colors, which triggers a ctypes incompatibility with Python ≥ 3.14.  Baking
    the color into vertex colors avoids any texture upload while still giving each part
    its correct color.
    """
    import trimesh

    m = mesh.copy()
    color = np.array([180, 180, 180, 255], dtype=np.uint8)  # neutral gray fallback
    v = mesh.visual
    if hasattr(v, "material") and hasattr(v.material, "to_pbr"):
        pbr = v.material.to_pbr()
        c = getattr(pbr, "baseColorFactor", None)
        if c is not None:
            color = np.clip(np.array(c), 0, 255).astype(np.uint8)
    n = len(m.vertices)
    m.visual = trimesh.visual.ColorVisuals(mesh=m, vertex_colors=np.tile(color, (n, 1)))
    return m


def build_pyrender_scene(tm_scene: "trimesh.scene.Scene") -> "pyrender.Scene":  # type: ignore[name-defined]
    import pyrender
    import trimesh

    scene = pyrender.Scene(bg_color=[0.95, 0.95, 0.95, 1.0], ambient_light=[0.35, 0.35, 0.35])
    for name, mesh in tm_scene.geometry.items():
        if not isinstance(mesh, trimesh.Trimesh):
            continue
        try:
            pr_mesh = pyrender.Mesh.from_trimesh(_bake_color(mesh), smooth=False)
        except Exception:
            continue
        try:
            node_transform = tm_scene.graph.get(name)[0]
        except Exception:
            node_transform = np.eye(4)
        scene.add(pr_mesh, pose=node_transform)
    return scene


def camera_pose(
    center: np.ndarray, cam_dist: float, elevation_deg: float = 25.0, azimuth_deg: float = -60.0
) -> np.ndarray:
    """Return a 4×4 camera pose (camera-to-world) looking at *center*."""
    theta = np.radians(elevation_deg)
    phi = np.radians(azimuth_deg)
    cam_pos = center + cam_dist * np.array([np.cos(theta) * np.cos(phi), np.cos(theta) * np.sin(phi), np.sin(theta)])
    forward = center - cam_pos
    forward /= np.linalg.norm(forward)
    up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    up_fixed = np.cross(right, forward)
    pose = np.eye(4)
    pose[:3, 0] = right
    pose[:3, 1] = up_fixed
    pose[:3, 2] = -forward
    pose[:3, 3] = cam_pos
    return pose


def render_urdf(urdf_path: str, out_path: str, size: int = 400) -> bool:
    """Render *urdf_path* to a PNG at *out_path*.  Returns True on success."""
    import pyrender
    import yourdfpy

    robot = yourdfpy.URDF.load(urdf_path)
    tm_scene = robot.scene

    if tm_scene.bounds is None:
        print(f"  [skip] {os.path.basename(urdf_path)} – no visual geometry found")
        return False

    pr_scene = build_pyrender_scene(tm_scene)

    bounds = tm_scene.bounds
    center = (bounds[0] + bounds[1]) / 2.0
    extent = float(np.max(bounds[1] - bounds[0]))
    cam_dist = extent * 2.2

    cam = camera_pose(center, cam_dist)
    pr_scene.add(pyrender.PerspectiveCamera(yfov=np.pi / 5), pose=cam)
    pr_scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=4.0), pose=cam)
    # Softer fill light from the opposite side to reduce harsh shadows.
    fill = camera_pose(center, cam_dist, elevation_deg=10.0, azimuth_deg=120.0)
    pr_scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=1.5), pose=fill)

    renderer = pyrender.OffscreenRenderer(size, size)
    try:
        color, _ = renderer.render(pr_scene)
    finally:
        renderer.delete()

    from PIL import Image

    Image.fromarray(color).save(out_path)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent.parent / "docs" / "images"),
        help="Directory to write images to (default: docs/images)",
    )
    parser.add_argument("--size", type=int, default=400, help="Square image resolution in pixels (default: 400)")
    parser.add_argument("--models", nargs="+", default=None, help="Render only the listed model names")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_names = args.models if args.models else airo_models.AIRO_MODEL_NAMES
    ok, skipped, failed = [], [], []

    for name in model_names:
        out_path = str(out_dir / f"{name}.png")
        print(f"Rendering {name} → {out_path}")
        try:
            success = render_urdf(airo_models.get_urdf_path(name), out_path, size=args.size)
            (ok if success else skipped).append(name)
        except Exception as e:
            print(f"  [error] {name}: {e}")
            failed.append(name)

    print(f"\nDone: {len(ok)} rendered, {len(skipped)} skipped (no geometry), {len(failed)} errors.")
    if failed:
        print(f"  Errors: {failed}")


if __name__ == "__main__":
    main()
