# Day 1 - Version 2: C++ VectorIndex and pybind11 Binding

## Goal

Implement the smallest useful C++ retrieval core and expose it to Python.

## What This Version Contains

- `cpp/CMakeLists.txt` for the native extension build
- `VectorIndex` with:
  - `add_item`
  - `search`
  - `size`
  - `dimension`
- pybind11 binding module `_vector_index`
- Python wrapper `VectorRetriever`
- local build script `scripts/build_extension.py`
- smoke test entry point `test_binding.py`

## Design Notes

- Metadata is intentionally kept out of C++ in Day 1.
- The index stores `id + embedding + norm`, which keeps the interface small and useful.
- Search uses cosine similarity with a bounded min-heap for top-k selection.
- The Python wrapper normalizes input handling and surfaces a clearer build error message.

## Thought Process

- Day 1 focuses on the minimal closed loop, not final architecture completeness.
- I chose a direct pybind11 binding over a more elaborate packaging flow because the acceptance target is local build + local invocation.
- Visual Studio's bundled CMake is used so the project does not depend on system-wide CMake PATH setup.

## Test Status

- Build script prepared
- Smoke test prepared
- Runtime validation will be completed in the next version after native compilation succeeds

## Next Step

Compile the extension, run `python test_binding.py`, capture the validation results, and push the verified version.
