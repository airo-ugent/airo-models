"""Visualize an airo-models URDF in the browser using viser.

Shows the visual and/or collision meshes and provides GUI sliders to move the
actuated joints. Run with a known model name (see ``AIRO_MODEL_NAMES``) or a
path to any URDF file:

    python scripts/visualize_urdf.py ur5e
    python scripts/visualize_urdf.py robotiq_2f_85 --collision
    python scripts/visualize_urdf.py path/to/robot.urdf

Then open the printed URL (default http://localhost:8080) in your browser.

Requires the optional visualization dependencies::

    pip install airo-models[viz]
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import viser
import viser.transforms as vtf
import yourdfpy
from viser.extras import ViserUrdf

# Allow running from a git clone (python scripts/visualize_urdf.py) without
# having installed the package: make the repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import airo_models  # noqa: E402


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


def main() -> None:  # noqa: C901
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", help="A known model name (e.g. 'ur5e') or a path to a URDF file.")
    parser.add_argument("--collision", action="store_true", help="Also load the collision meshes.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to serve on (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on (default: 8080).")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Reload the URDF live whenever the file changes on disk (keeps joint positions).",
    )
    args = parser.parse_args()

    urdf_path = resolve_urdf_path(args.model)
    print(f"Loading URDF: {urdf_path}")

    server = viser.ViserServer(host=args.host, port=args.port)

    # A separate yourdfpy model is kept purely for forward kinematics, so we can
    # place a coordinate frame at every link without depending on ViserUrdf
    # internals.
    fk_ref = [yourdfpy.URDF.load(urdf_path)]
    link_names = [name for name in fk_ref[0].link_map]

    def build_scene() -> ViserUrdf:
        server.scene.reset()
        server.scene.add_grid("/grid", width=2.0, height=2.0)
        return ViserUrdf(
            server,
            Path(urdf_path),
            load_meshes=True,
            load_collision_meshes=args.collision,
        )

    # Mutable container so GUI callbacks and the watch loop share the current model.
    urdf_ref = [build_scene()]

    # Visibility toggles for visual and (optionally) collision meshes.
    with server.gui.add_folder("Display"):
        show_visual = server.gui.add_checkbox("Show visual", initial_value=True)
        show_visual.on_update(lambda _: setattr(urdf_ref[0], "show_visual", show_visual.value))
        show_collision = None
        if args.collision:
            show_collision = server.gui.add_checkbox("Show collision", initial_value=True)
            show_collision.on_update(lambda _: setattr(urdf_ref[0], "show_collision", show_collision.value))

    # One coordinate frame per link. Handles are re-created on reload; the GUI
    # checkboxes below persist and drive their visibility.
    frame_handles: dict[str, viser.FrameHandle] = {}

    def add_link_frames() -> None:
        frame_handles.clear()
        for link_name in link_names:
            frame_handles[link_name] = server.scene.add_frame(
                f"/link_frames/{link_name}",
                show_axes=True,
                axes_length=frame_size.value,
                axes_radius=frame_size.value * 0.08,
                origin_radius=0.0,
            )

    def update_frame_poses() -> None:
        cfg = np.array([s.value for s in slider_handles])
        fk_ref[0].update_cfg(cfg)
        base = fk_ref[0].base_link
        for link_name, handle in frame_handles.items():
            transform = fk_ref[0].get_transform(link_name, base)
            handle.position = transform[:3, 3]
            handle.wxyz = vtf.SO3.from_matrix(transform[:3, :3]).wxyz

    def update_frame_visibility() -> None:
        for link_name, handle in frame_handles.items():
            handle.visible = show_frames.value and link_toggles[link_name].value

    # Link-frame controls: a master toggle, an axis-size slider and one checkbox
    # per link so individual frames can be shown in isolation.
    with server.gui.add_folder("Link frames"):
        show_frames = server.gui.add_checkbox("Show link frames", initial_value=True)
        frame_size = server.gui.add_slider("Axis size", min=0.01, max=0.3, step=0.005, initial_value=0.05)
        link_toggles: dict[str, Any] = {}
        with server.gui.add_folder("Per-link"):
            for link_name in link_names:
                link_toggles[link_name] = server.gui.add_checkbox(link_name, initial_value=True)

    show_frames.on_update(lambda _: update_frame_visibility())
    for link_name in link_names:
        link_toggles[link_name].on_update(lambda _: update_frame_visibility())

    def _resize_frames(_: Any) -> None:
        add_link_frames()
        update_frame_poses()
        update_frame_visibility()

    frame_size.on_update(_resize_frames)

    # One slider per actuated joint; initialise at the middle of each range.
    joint_limits = urdf_ref[0].get_actuated_joint_limits()
    slider_handles: list[Any] = []
    initial_config: list[float] = []
    with server.gui.add_folder("Joints"):
        reset_button = server.gui.add_button("Reset")
        for joint_name, (lower, upper) in joint_limits.items():
            lower = lower if lower is not None else -np.pi
            upper = upper if upper is not None else np.pi
            initial = 0.0 if lower < 0.0 < upper else (lower + upper) / 2.0
            slider = server.gui.add_slider(
                label=joint_name,
                min=lower,
                max=upper,
                step=1e-3,
                initial_value=initial,
            )

            def _on_joint(_: Any) -> None:
                urdf_ref[0].update_cfg(np.array([s.value for s in slider_handles]))
                update_frame_poses()

            slider.on_update(_on_joint)
            slider_handles.append(slider)
            initial_config.append(initial)

    @reset_button.on_click
    def _(_: Any) -> None:
        for slider, value in zip(slider_handles, initial_config):
            slider.value = value

    urdf_ref[0].update_cfg(np.array(initial_config))
    add_link_frames()
    update_frame_poses()
    update_frame_visibility()

    print(f"Serving at http://localhost:{args.port} (Ctrl+C to stop)")
    if args.watch:
        print(f"Watching {urdf_path} for changes (auto-reload enabled).")
    last_mtime = os.path.getmtime(urdf_path)
    while True:
        time.sleep(0.5)
        if not args.watch:
            continue
        try:
            mtime = os.path.getmtime(urdf_path)
        except OSError:
            continue
        if mtime == last_mtime:
            continue
        last_mtime = mtime
        cfg = np.array([s.value for s in slider_handles])
        try:
            fk_ref[0] = yourdfpy.URDF.load(urdf_path)
            urdf_ref[0] = build_scene()
            urdf_ref[0].update_cfg(cfg)
            urdf_ref[0].show_visual = show_visual.value
            if show_collision is not None:
                urdf_ref[0].show_collision = show_collision.value
            add_link_frames()
            update_frame_poses()
            update_frame_visibility()
            print(f"Reloaded {urdf_path}", flush=True)
        except Exception as e:
            print(f"Reload failed ({e}); keeping previous model.", flush=True)


if __name__ == "__main__":
    main()
