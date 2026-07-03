# RealMan RM75-6F

7-DoF arm from RealMan Robotics. URDF and meshes sourced from
[RealManRobot/rm_models](https://github.com/RealManRobot/rm_models/tree/main/RM75/urdf/RM75-6F).

Two extra frames follow the ROS-Industrial convention (see
[`frame_conventions.md`](../../frame_conventions.md)): a `base` frame coincident
with `base_link` and a `tool0` flange frame coincident with `link_7`. Per
RealMan's official URDFs and driver, neither is rotated about z relative to the
manufacturer's base/tool frames.

## Collision variants

Three models are provided, differing only in their collision geometry. Visual
meshes, kinematics and frames are identical.

| Model name | Collision geometry | Use for |
|---|---|---|
| `rm75_6f_convex_collision` | 64 convex hulls (CoACD, ≤64 verts each) | **Default** — motion planning |
| `rm75_6f_primitives` | 8 bounding cylinders | Fastest checks / coarse reachability |
| `rm75_6f` | Raw visual meshes | Visualization / highest-fidelity checks |

- **`rm75_6f_convex_collision` (recommended default)** — Approximate convex
  decomposition of each link. Convex geometry is required by most planners and
  is a good balance of accuracy and query speed. Faster than the raw meshes and
  much tighter-fitting than the primitives.
- **`rm75_6f_primitives`** — One bounding cylinder per link (link 2/4/6
  horizontal, others vertical). Cheapest collision queries, but over-approximates
  the arm volume, so it reports false positives in tight spaces.
- **`rm75_6f`** — The original concave visual meshes used directly as collision
  geometry. Highest fidelity but concave (unsuitable for some planners) and the
  slowest to query.

## Regenerating the collision variants

Both variants are generated from `rm75_6f.urdf` with reusable scripts (needs the
`collision` extra: `pip install airo-models[collision]`):

```bash
python scripts/generate_convex_collision_meshes.py rm75_6f      # -> rm75_6f_convex_collision.urdf + collision_convex/
python scripts/generate_primitive_collision_meshes.py rm75_6f \
    --axis-map link_2:y,link_4:y,link_6:y,link_7:z              # -> rm75_6f_primitives.urdf
```
