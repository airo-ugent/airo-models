# airo-models
Curated URDFs and 3D models of the robots and gripper used at airo.

## Installation
`airo-models` is available on PyPi and can be installed with pip:
```
pip install airo-models
```

## Usage
Example of loading a URDF from airo-models, customizing it and writing it to a temporary file:
```python
import airo_models

robotiq_urdf_path = airo_models.get_urdf_path("robotiq_2f_85")
robotiq_urdf = airo_models.urdf.read_urdf(robotiq_urdf_path)

# Make the robotiq gripper static
airo_models.urdf.replace_value(robotiq_urdf, "@type", "revolute", "fixed")
airo_models.urdf.delete_key(robotiq_urdf, "mimic")
airo_models.urdf.delete_key(robotiq_urdf, "transmission")

# Write it to a temporary file to read later with Drake's AddModelFromFile
robotiq_static_urdf_path = airo_models.urdf.write_urdf_to_tempfile(
    robotiq_urdf, robotiq_urdf_path, prefix="robotiq_2f_85_static_"
)
```

To check which models are available:
```python
from airo_models.files import AIRO_MODEL_NAMES

print(AIRO_MODEL_NAMES)

>>> ['ur3e', 'ur5e', 'robotiq_2f_85']
```

### URDF Primitives
The `airo_models` package provides convenient functions to generate URDFs for basic geometric shapes without needing to write URDF files by hand. This is useful for creating collision geometries, obstacles, or simple models.

Supported shapes are: **box**, **sphere**, **cylinder**, and **mesh**. Each shape has four functions available for different use cases:

1. `{shape}_geometry_dict(...)` — Returns a dictionary representation of just the geometry. Use this to embed a primitive in a more complex URDF structure.
2. `{shape}_dict(...)` — Returns a dictionary representation of a complete single-link URDF model. Use this to manipulate the URDF as a dictionary (e.g., to edit properties).
3. `{shape}_urdf(...)` — Returns the URDF as an XML string. Use this to inspect or write the URDF to a file.
4. `{shape}_urdf_path(...)` — Generates and writes the URDF to a temporary file, returning the path. Use this when you need to load the URDF into a simulator or robotics library.

All shape functions accept `name` and (optionally) `rgba` parameters to customize the model name and visual color. The URDF follows the modeling convention: X+ forward, Z+ up, with the origin at the center of the shape.

#### Examples

Generate a box URDF and get the path for use with Drake or another simulator:
```python
import airo_models

# Create a red box with dimensions (0.5, 1.0, 2.0) meters
box_path = airo_models.box_urdf_path(size=(0.5, 1.0, 2.0), name="my_box", rgba=(1.0, 0.0, 0.0, 1.0))
```

Create a sphere and inspect the XML:
```python
# Create a yellow sphere with radius 0.1 meters
sphere_xml = airo_models.sphere_urdf(radius=0.1, name="ball", rgba=(1.0, 1.0, 0.0, 1.0))
print(sphere_xml)
```

Generate a cylinder as a dictionary for further manipulation:
```python
# Create a cylinder and modify it
cyl_dict = airo_models.cylinder_dict(length=1.0, radius=0.05, name="rod")
# Now you can edit cyl_dict using airo_models.urdf functions before writing it
```

Wrap an existing mesh file:
```python
# Load a mesh file into a URDF
mesh_path = airo_models.mesh_urdf_path("/path/to/your/model.obj", name="custom_object")
```

## Visualization
You can visualize any model in your browser (visual and/or collision meshes, coordinate frames for every link, with sliders to move the joints) using the `visualize_urdf.py` script, which is powered by [viser](https://github.com/nerfstudio-project/viser).

Install the optional visualization dependencies:
```
pip install airo-models[viz]
```

Then run it with a known model name (see `AIRO_MODEL_NAMES`) or a path to any URDF file:
```
python scripts/visualize_urdf.py ur5e                # visual meshes only
python scripts/visualize_urdf.py robotiq_2f_85 --collision   # also load collision meshes
python scripts/visualize_urdf.py path/to/robot.urdf --watch   # live-reload on file changes
```
Open the printed URL (default http://localhost:8080) in your browser. The GUI lets you
toggle the visual/collision geometry, show per-link coordinate frames (globally or per link),
and move the actuated joints. Use `--watch` to auto-reload the model whenever the URDF file
changes on disk (handy while hand-tuning collision primitives).

## Modeling conventions
The standard convention we follow is X+ forward, Z+ up.

For cameras, we follow Z+ forward through the eye of the camera, X+ right. The origin of the camera is at the center of the (left) lens. Left is defined egocentric of the camera (i.e. looking out of the eyes of the camera).

For grippers, we follow Z+ pointing outwards from the fingers and X in the direction in which the parallel gripper closes its fingers. The origin of the gripper (`base_link`) is at the mounting point of its base.

## Development
### Local installation

- Clone this repo
- Install the dependencies using `uv sync`
- Initialize the pre-commit hooks `uv run pre-commit install`
- Run the tests with `uv run pytest .`

### Releasing
Releasing to PyPi is done automatically by github actions when a new tag is pushed to the main branch.
1. Update the version in `pyproject.toml`.
2. ``` git add pyproject.toml```
3. ``` git commit -m ""```
4. ``` git push```
5. ```git tag -a v0.1.0 -m "airo-models v0.1.0"```
6. ```git push origin v0.1.0```

This was set up following [this guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/) first and then [this guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).