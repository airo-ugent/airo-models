# airo-models
Curated URDFs and 3D models of the robots and gripper used at airo.

## Installation
```
pip install git+https://github.com/airo-ugent/airo-models@main
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

>>> ['ur3e', 'ur5e', 'robotif_2f_85']
```

### Local installation

- clone this repo
- create the conda environment `conda env create -f environment.yaml`
- initialize the pre-commit hooks `pre-commit install`
