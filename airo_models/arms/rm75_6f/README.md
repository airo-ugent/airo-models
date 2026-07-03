# RealMan RM75-6F

7-DoF arm from RealMan Robotics. URDF and meshes sourced from
[RealManRobot/rm_models](https://github.com/RealManRobot/rm_models/tree/main/RM75/urdf/RM75-6F).

Two extra frames follow the ROS-Industrial convention (see
[`frame_conventions.md`](../../frame_conventions.md)): a `base` frame coincident
with `base_link` and a `tool0` flange frame coincident with `link_7`. Per
RealMan's official URDFs and driver, neither is rotated about z relative to the
manufacturer's base/tool frames.

## Collision variants

Two models are provided. They share identical visual meshes, kinematics and
frames, and differ only in their collision geometry.

| Model name | Collision geometry | Use for |
|---|---|---|
| `rm75_6f` | 64 convex hulls (CoACD, <=64 verts each) | **Default** -- motion planning |
| `rm75_6f_primitives` | 8 bounding cylinders | Fastest checks / coarse reachability |

- **`rm75_6f` (recommended default)** -- Approximate convex decomposition of each
  link's visual mesh. Convex geometry is required by most planners and offers a
  good balance of accuracy and query speed.
- **`rm75_6f_primitives`** -- One bounding cylinder per link (link 2/4/6
  horizontal, others vertical). Cheapest collision queries, but over-approximates
  the arm volume, so it reports false positives in tight spaces.

## Regenerating the collision variants

Both variants are derived from the **visual** meshes referenced in `rm75_6f.urdf`
with reusable scripts (needs the `collision` extra:
`pip install airo-models[collision]`):

```bash
# Convex collision (writes collision/ + updates rm75_6f.urdf in place):
python scripts/generate_convex_collision_meshes.py rm75_6f \
    --output-urdf airo_models/arms/rm75_6f/rm75_6f.urdf \
    --output-mesh-dir airo_models/arms/rm75_6f/collision

# Primitive collision (writes rm75_6f_primitives.urdf):
python scripts/generate_primitive_collision_meshes.py rm75_6f \
    --axis-map link_2:y,link_4:y,link_6:y,link_7:z
```
