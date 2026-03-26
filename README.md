# Codebase Copilot

Codebase Copilot is a local code-repository Q&A agent built with Python and C++.

## Day 1 Scope

Day 1 only targets the smallest C++/Python retrieval loop:

- scaffold the repository
- build a pybind11 native module with CMake
- implement a minimal `VectorIndex`
- call the native module from Python
- verify the result with `python test_binding.py`

## Current Layout

```text
cpp/
python/
scripts/
tests/
docs/
```

## Day 1 Build

1. Install the local dependency bundle:
   `python -m pip install --target .vendor pybind11==2.13.6`
2. Build the native extension:
   `python scripts/build_extension.py`
3. Run the smoke test:
   `python test_binding.py`

## Version Notes

- `docs/day1_v1_project_scaffold.md`
- `docs/day1_v2_cpp_binding.md`
- `docs/day1_v3_validation.md`

## Repository Rules

- `autumn_project1.md` is intentionally excluded from version control.
- Each delivery version is accompanied by a matching note in `docs/`.
