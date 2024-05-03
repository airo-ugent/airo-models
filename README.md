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

## Modeling conventions
The standard convention we follow is X+ forward, Z+ up.

For cameras, we follow Z+ forward through the eye of the camera, X+ right. The origin of the camera is at the center of the (left) lens. Left is defined egocentric of the camera (i.e. looking out of the eyes of the camera).

For grippers, we follow Z+ pointing outwards from the fingers and X in the direction in which the parallel gripper closes its fingers. The origin of the gripper (`base_link`) is at the mounting point of its base.

## Development
### Local installation

- Clone this repo
- Create the conda environment `conda env create -f environment.yaml`
- Initialize the pre-commit hooks `pre-commit install`
- Run the tests with `pytest .`

### Releasing
Releasing to PyPi is done automatically by github actions when a new tag is pushed to the main branch.
1. Update the version in `pyproject.toml`.
2. ``` git add pyproject.toml```
3. ``` git commit -m ""```
4. ``` git push```
5. ```git tag -a v0.1.0 -m "airo-models v0.1.0"```
6. ```git push origin v0.1.0```

This was set up following [this guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/) first and then [this guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).