# airo-models
Curated URDFs and 3D models of the robots and gripper used at airo.

## Installation
`airo-models` is available on PyPi and can be installed with pip:
```
pip install airo-models
```

## Usage
Get the path to a URDF file by a name:
```python
from airo_models.utils import get_urdf_path

ur5e_path = get_urdf_path("ur5e")
```

To check which models are available:
```python
from airo_models.utils import AIRO_MODEL_NAMES

print(AIRO_MODEL_NAMES)

>>> ['ur3e', 'ur5e', 'robotiq_2f_85']
```

### Local installation

- clone this repo
- create the conda environment `conda env create -f environment.yaml`
- initialize the pre-commit hooks `pre-commit install`

## Releasing
Releasing to PyPi is done automatically by github actions when a new tag is pushed to the main branch.
1. Update the version in `pyproject.toml`.
2. ```git tag -a v0.1.0 -m "airo-models v0.1.0"```
3. ```git push origin v0.1.0```

This was set up following [this guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/) first and then [this guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).