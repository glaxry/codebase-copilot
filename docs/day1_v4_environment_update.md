# Day 1 - Version 4: Switch to Environment-Based Dependencies

## Goal

Stop relying on a repository-local `.vendor` directory in normal usage and use the active Python environment directly.

## What Changed

- `scripts/build_extension.py` now prefers `pybind11` from the active environment
- the build instructions now use `python -m pip install -r requirements.txt`
- the recommended workflow explicitly targets the `codebase` environment

## Why This Change

- the user has already created a dedicated `codebase` environment
- environment-based dependency management is simpler than keeping a local vendored package directory
- future build and test commands now match normal Python project workflows

## Current Run Steps

```powershell
conda activate codebase
cd "D:\Autumn Campus Recruitmen\Codebase Copilot"
python -m pip install -r requirements.txt
python scripts/build_extension.py
python test_binding.py
```

## Notes

- `.vendor` is no longer required in the normal workflow
- the build script only falls back to `.vendor` as a compatibility path if the active environment does not provide `pybind11`
- the compiled extension is still generated into `python/codebase_copilot/`
