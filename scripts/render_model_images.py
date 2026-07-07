"""Render a preview image for every registered airo-models URDF and compose them
into an animated GIF gallery (``docs/images/gallery.gif``).

Run from the repo root:

    python scripts/render_model_images.py

Optional arguments:

    --output-dir PATH    Directory to write images to (default: docs/images)
    --size N             Square model image resolution in pixels (default: 320)
    --models A B ...     Render only the listed model names (skips GIF generation)
    --frame-ms N         Milliseconds per GIF frame (default: 2000)

Requires the ``render`` optional dependencies:

    pip install airo-models[render]
"""

import argparse
import os
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import airo_models

# Gallery display order: (category label, [model names]).
# Only canonical models are shown; variant/sub-part names are rendered to PNG
# but excluded from the GIF.
GALLERY_GROUPS: list[tuple[str, list[str]]] = [
    ("Arms", ["ur3e", "ur5e", "rm75_6f"]),
    ("Grippers", ["robotiq_2f_85", "schunk_egk40", "schunk_egk40_magneto"]),
    ("Cameras", ["zed2i", "zedm", "d435"]),
    ("Mobile platforms", ["kelo_robile_battery", "kelo_robile_cpu", "kelo_robile_wheel"]),
    ("Environment", ["table8080", "mounting_plate_ur3e", "mounting_plate_ur5e"]),
]


def _bake_color(mesh: Any) -> Any:
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


def build_pyrender_scene(tm_scene: Any) -> Any:
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


def build_gallery_gif(out_dir: Path, size: int = 320, frame_ms: int = 2000) -> None:
    """Compose per-model PNGs from *out_dir* into an animated GIF gallery."""
    from PIL import Image, ImageDraw, ImageFont

    font_path_bold = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    font_path_reg = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

    pad = 16
    label_h = 48
    cat_h = 32
    w = size + 2 * pad
    h = cat_h + size + label_h + 2 * pad

    try:
        font_cat = ImageFont.truetype(font_path_bold, 16)
        font_name = ImageFont.truetype(font_path_reg, 17)
    except OSError:
        font_cat = font_name = ImageFont.load_default()  # type: ignore[assignment]

    bg = (245, 245, 245)
    frames: list[Image.Image] = []

    for category, models in GALLERY_GROUPS:
        for model in models:
            img_path = out_dir / f"{model}.png"
            if not img_path.exists():
                print(f"  [gif] skipping {model} – PNG not found")
                continue

            frame = Image.new("RGB", (w, h), bg)
            draw = ImageDraw.Draw(frame)

            # Category banner
            draw.rectangle([0, 0, w, cat_h], fill=(40, 40, 40))
            bbox = font_cat.getbbox(category)
            tx = (w - (bbox[2] - bbox[0])) // 2
            ty = (cat_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
            draw.text((tx, ty), category, font=font_cat, fill=(255, 255, 255))

            # Model image
            model_img = Image.open(img_path).convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
            frame.paste(model_img, (pad, cat_h + pad))

            # Model name
            label_y = cat_h + pad + size
            bbox2 = font_name.getbbox(model)
            tx2 = (w - (bbox2[2] - bbox2[0])) // 2
            ty2 = label_y + (label_h - (bbox2[3] - bbox2[1])) // 2 - bbox2[1]
            draw.text((tx2, ty2), model, font=font_name, fill=(30, 30, 30))

            frames.append(frame)

    if not frames:
        print("  [gif] no frames – skipping gallery.gif")
        return

    gif_path = out_dir / "gallery.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_ms,
        loop=0,
        optimize=False,
    )
    print(f"\nSaved {gif_path}  ({len(frames)} frames, {gif_path.stat().st_size // 1024} KB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent.parent / "docs" / "images"),
        help="Directory to write images to (default: docs/images)",
    )
    parser.add_argument("--size", type=int, default=320, help="Square model image resolution in pixels (default: 320)")
    parser.add_argument(
        "--models", nargs="+", default=None, help="Render only the listed model names (skips GIF generation)"
    )
    parser.add_argument("--frame-ms", type=int, default=2000, help="Milliseconds per GIF frame (default: 2000)")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_names = args.models if args.models else airo_models.AIRO_MODEL_NAMES
    ok: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

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

    if args.models is None:
        build_gallery_gif(out_dir, size=args.size, frame_ms=args.frame_ms)


if __name__ == "__main__":
    main()
