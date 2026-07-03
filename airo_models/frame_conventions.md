# AIRO model frame naming conventions

Our conventions are mostly derrived from ROS (see below).


For arms, we expect two frames:
-  a `base` frame that corresponds with the base frame of the manufacturer, which is usually z-upward, but rotation around z-axis can differ.
- a `tool0` frame at the flange, corresponding to the manufacturer tool frame,  which is usually z-forward.

For end-effectors such as grippers, we expect:
- a `tool0` frame that corresponds to the mechanical interface with the robot arm.





# ROS Frame Naming Conventions

Frame naming in ROS isn't a single spec but a few overlapping conventions: **REP 103** (units and coordinate conventions), **REP 105** (frame names for mobile platforms), and the **ROS-Industrial** conventions layered on top for manipulators.

## Coordinate conventions (REP 103)

- Body-attached frames are right-handed: **x forward, y left, z up**, rotations counterclockwise-positive.
- **Camera frames are the exception**: they use the optical convention (**z forward, x right, y down**) and carry an `_optical` suffix.
- The tf tree usually holds both `camera_link` (body convention) and `camera_color_optical_frame` (optical convention). The ~90° rotation between them is a classic source of hand-eye calibration sign errors.

## Base frame

- `base_link` — REP-103-compliant root of the kinematic chain (z-up), provided by ROS-Industrial support packages.
- `base` — the manufacturer's native base frame, which may differ in orientation. On UR arms, `base` and `base_link` are rotated 180° about z.

## Links and joints

- **Generic numeric**: `link_1`…`link_n`, `joint_1`…`joint_n` — common in industrial support packages.
- **Descriptive**: used where morphology is fixed. UR example:
  - Links: `shoulder_link`, `upper_arm_link`, `forearm_link`, `wrist_1_link`, `wrist_2_link`, `wrist_3_link`
  - Joints: `shoulder_pan_joint`, `shoulder_lift_joint`, `elbow_joint`, `wrist_1/2/3_joint`

## End-effector frames

| Frame | Meaning |
|-------|---------|
| `tool0` | ROS-Industrial standard "tool zero": all-zeros frame coincident with the mechanical flange, oriented per the manufacturer's convention (typically z out of the flange). The stable endpoint every support package publishes. |
| `flange` | Introduced later to give a REP-103-oriented frame (x outward) at the same location. Not always provided. |
| `tcp` / `tool_center_point` | The functional tool point (fingertip contact, focal point), defined as a fixed transform off `tool0`/`flange`. Usually set as the MoveIt end-effector link. |
| `ee_link` | Generic end-effector link seen in older MoveIt configs; the `tool0` + explicit TCP pattern is cleaner. |

## Cameras

Camera frames are the main exception to REP 103 and the most common source of transform errors.

- **`_optical` frames** use the optical convention: **z forward (into the scene), x right, y down**. This is what image geometry and projection math expect.
- **Non-optical frames** (e.g. `camera_link`) follow the standard body convention (**x forward, y left, z up**), matching the physical mounting.
- A driver typically publishes both, with a fixed ~90° rotation between them. Conventional names:
  - `camera_link` — physical body frame, root of the camera's tf subtree.
  - `camera_color_optical_frame`, `camera_depth_optical_frame`, `camera_infra1_optical_frame` — per-stream optical frames (RealSense-style naming).
- **Rule**: use the `_optical` frame for anything involving pixels, projection, or point clouds; use the body frame for mounting and physical reasoning. Publishing hand-eye results into the wrong one is the classic sign-flip / 90° bug.
- Multiple cameras are namespaced by prefix: `wrist_camera_link`, `wrist_camera_color_optical_frame`, `front_camera_link`, etc.

## Mobile robots (REP 105)

REP 105 defines a standard frame chain for mobile platforms, ordered from most stable to most local:

| Frame | Role |
|-------|------|
| `map` | World-fixed frame. Accurate long-term but discrete jumps on localization updates. Not smooth. |
| `odom` | World-fixed, continuous and smooth (from wheel/visual/inertial odometry) but drifts over time. |
| `base_link` | Rigidly attached to the robot body, at its reference point. |
| `base_footprint` | Optional 2D projection of `base_link` onto the ground plane (z = 0). |

- **Chain**: `map → odom → base_link`. Each frame has exactly one parent, so `map → base_link` is expressed *through* `odom` — localization publishes `map → odom` (the drift correction), while odometry publishes `odom → base_link`.
- **Why both `map` and `odom`**: use `odom` for local, short-term motion control (smooth, no jumps); use `map` for global goals (accurate, but jumps on correction).
- **`earth`** is the optional parent of multiple `map` frames for multi-robot / global (ECEF) setups.
- Sensors hang off `base_link` with descriptive names: `laser`/`lidar_link`, `imu_link`, `camera_link`, etc.

## Rule of thumb

Attach the gripper/hand URDF to `tool0` (or `flange`), define a named TCP frame at the actual working point, and drive planning off that. Keeping the manufacturer chain terminating at `tool0` untouched keeps the support package swappable.

A sensible full tree:

```
base_link → … → tool0 → hand_base → tcp
                    └→ camera_link → camera_color_optical_frame
```