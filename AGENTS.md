# AGENTS.md

Guidance for AI coding agents working in the `airo-models` repository.

## Project overview

`airo-models` is a Python package that provides curated URDFs and 3D models
of the robots, grippers, cameras and environment objects used at AIRO
(Ghent University). It is published to PyPI as `airo-models`.

The package exposes:
- `airo_models.get_urdf_path(name)` — resolve a model name (e.g. `"ur5e"`) to
  the absolute path of its bundled URDF file.
- `airo_models.AIRO_MODEL_NAMES` — list of known model names.
- `airo_models.urdf` — helpers to read, edit (delete keys, replace values,
  make static, make paths absolute) and write URDFs as Python dictionaries via
  `xmltodict`.
- `airo_models.primitives` — helpers to generate URDFs for primitive shapes
  (box, cylinder, mesh, sphere).

## Repository layout

- `airo_models/` — the package source.
  - `files.py` — model-name-to-URDF-path registry (`get_urdf_path`,
    `AIRO_MODEL_NAMES`). Add new models here.
  - `urdf.py` — URDF read/write and dictionary manipulation utilities.
  - `primitives/` — box, cylinder, mesh, sphere URDF generators.
  - `arms/`, `grippers/`, `cameras/`, `mobile_platforms/`, `environment/` —
    the actual URDF and mesh assets, grouped by category.
- `test/` — pytest tests (`test_*.py`).
- `visualize_urdf.py` — browser-based URDF viewer (viser); run
  `python visualize_urdf.py <name|path> [--collision]`. Needs the `viz` extra
  (`pip install airo-models[viz]`).
- `notebooks/` — example notebooks (stripped with `nbstripout` on commit).
- `environment.yaml` — conda environment used by CI.
- `pyproject.toml` — package metadata and dependencies.
- `setup.cfg` — mypy, flake8 and pytest configuration.

## Development setup

The README recommends `uv`:

```bash
uv sync                      # install dependencies
uv run pre-commit install    # install git hooks
```

CI uses a conda/micromamba environment defined in `environment.yaml`.

## Build / lint / test commands

Run these before finishing a change. Prefix with `uv run` if using uv.

- Tests: `pytest .`
- Type checking: `mypy .`
- Formatting & linting (all hooks): `pre-commit run --all-files`

CI enforces all three (see `.github/workflows/`): pytest, mypy and pre-commit
must pass.

## Conventions

- **Python** >= 3.10. Type annotations are required on all functions
  (`disallow_untyped_defs = True` in `setup.cfg`); modern syntax such as
  `str | None` is used.
- **Formatting**: black and isort, both with line length **119**
  (isort uses `--profile black`). flake8 max line length is 120.
- Unused imports/variables are stripped by autoflake via pre-commit.
- Prefer explicit `try`/`except` blocks over helper wrapper functions for
  error handling in scripts.
- **Modeling conventions**: X+ forward, Z+ up.
  - Cameras: Z+ forward through the lens, X+ right; origin at the center of the
    (left) lens.
  - Grippers: Z+ points outward from the fingers, X+ in the closing direction;
    origin (`base_link`) at the mounting point of the base.

## Adding a new model

1. Add the URDF and mesh assets under the appropriate category folder in
   `airo_models/` (e.g. `grippers/<name>/`).
2. Register the model in the `name_to_urdf_path` dict in
   `airo_models/files.py`.
3. If it should be part of the public list, add it to `AIRO_MODEL_NAMES`.
4. Add/adjust tests in `test/` (see `test_existence.py`).
5. Ensure non-python assets are included in the package (`MANIFEST.in`).

## Releasing

Releasing to PyPI is automated by GitHub Actions on a new tag pushed to `main`:

1. Bump `version` in `pyproject.toml` and commit.
2. Tag: `git tag -a v0.1.0 -m "airo-models v0.1.0"`.
3. `git push origin v0.1.0`.
