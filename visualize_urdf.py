"""Visualize an airo-models URDF in the browser using viser.

Shows the visual and/or collision meshes and provides GUI sliders to move the
actuated joints. Run with a known model name (see ``AIRO_MODEL_NAMES``) or a
path to any URDF file:

    python visualize_urdf.py ur5e
    python visualize_urdf.py robotiq_2f_85 --collision
    python visualize_urdf.py path/to/robot.urdf

Then open the printed URL (default http://localhost:8080) in your browser.

Requires the optional visualization dependencies::

    pip install viser yourdfpy
"""

import argparse
import os
import time
from pathlib import Path

import numpy as np
import viser
from viser.extras import ViserUrdf

import airo_models


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", help="A known model name (e.g. 'ur5e') or a path to a URDF file.")
    parser.add_argument("--collision", action="store_true", help="Also load the collision meshes.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to serve on (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve on (default: 8080).")
    args = parser.parse_args()

    urdf_path = resolve_urdf_path(args.model)
    print(f"Loading URDF: {urdf_path}")

    server = viser.ViserServer(host=args.host, port=args.port)
    server.scene.add_grid("/grid", width=2.0, height=2.0)

    viser_urdf = ViserUrdf(
        server,
        Path(urdf_path),
        load_meshes=True,
        load_collision_meshes=args.collision,
    )

    # Visibility toggles for visual and (optionally) collision meshes.
    with server.gui.add_folder("Display"):
        show_visual = server.gui.add_checkbox("Show visual", initial_value=True)
        show_visual.on_update(lambda _: setattr(viser_urdf, "show_visual", show_visual.value))
        if args.collision:
            show_collision = server.gui.add_checkbox("Show collision", initial_value=True)
            show_collision.on_update(lambda _: setattr(viser_urdf, "show_collision", show_collision.value))

    # One slider per actuated joint; initialise at the middle of each range.
    joint_limits = viser_urdf.get_actuated_joint_limits()
    slider_handles = []
    initial_config = []
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
            slider.on_update(lambda _: viser_urdf.update_cfg(np.array([s.value for s in slider_handles])))
            slider_handles.append(slider)
            initial_config.append(initial)

    @reset_button.on_click
    def _(_) -> None:
        for slider, value in zip(slider_handles, initial_config):
            slider.value = value

    viser_urdf.update_cfg(np.array(initial_config))

    print(f"Serving at http://localhost:{args.port} (Ctrl+C to stop)")
    while True:
        time.sleep(1.0)


if __name__ == "__main__":
    main()
