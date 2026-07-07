# RealMan RM75-6FB

7-DoF RM-75 arm with EEF Force-Torque sensor from RealMan Robotics — **6FB variant**
(link_7 is 11.3 mm shorter than the 6F variant: `joint_7 xyz="0 -0.1612 0"` vs `"0 -0.1725 0"`).

Two models are provided. They share identical visual meshes, kinematics and
frames, and differ only in their collision geometry.

| Model name | Collision geometry | Use for |
|---|---|---|
| `rm75_6fb` | 64 convex hulls (CoACD, ≤64 verts each) | **Default** — motion planning |
| `rm75_6fb_primitives` | 8 bounding cylinders | Fastest checks / coarse reachability |

## How the models were obtained

Original URDF and meshes sourced from
[RealManRobot/rm_models](https://github.com/RealManRobot/rm_models/tree/main/RM75/urdf/RM75-6FB).

Two extra frames added following the ROS-Industrial convention (see
[`frame_conventions.md`](../../frame_conventions.md)): a `base` frame coincident
with `base_link` and a `tool0` flange frame coincident with `link_7`.

## Collision variants

Both variants are derived from the **visual** meshes referenced in `rm75_6fb.urdf`
with reusable scripts (needs the `collision` extra:
`pip install airo-models[collision]`):

```bash
# Convex collision (writes collision/ + updates rm75_6fb.urdf in place):
python scripts/generate_convex_collision_meshes.py rm75_6fb \
    --output-urdf airo_models/arms/rm75_6fb/rm75_6fb.urdf \
    --output-mesh-dir airo_models/arms/rm75_6fb/collision

# Primitive collision (writes rm75_6fb_primitives.urdf):
python scripts/generate_primitive_collision_meshes.py rm75_6fb \
    --axis-map link_2:y,link_4:y,link_6:y,link_7:z
```

## Drake compatibility

The visual meshes are provided as `.obj` files (in `visual/`).
Drake does not support STL for visual geometry, so the original `.STL` files
from the upstream source were converted to `.obj` using `trimesh`:

```bash
cd airo_models/arms/rm75_6fb/visual
for stl in *.STL; do
    python3 -c "import trimesh; trimesh.load('$stl').export('${stl%.STL}.obj')"
done
```

The original `.STL` files are kept alongside the `.obj` files for reference.
