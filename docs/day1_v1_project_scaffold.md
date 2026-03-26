# Day 1 - Version 1: Project Scaffold

## Goal

Create a clean Day 1 workspace before writing the C++ binding:

- establish repository layout
- define ignore rules
- keep the source `autumn_project1.md` out of Git
- create a place for later build, test, and iteration notes

## What This Version Contains

- top-level `README.md`
- top-level `requirements.txt`
- Python package directory `python/codebase_copilot/`
- `docs/` directory for per-version notes
- `.gitignore` that excludes the source planning document and build outputs

## Design Notes

- The implementation follows the Day 1 target strictly: minimal C++/Python integration first.
- No Day 2 chunking or repository indexing code is added yet.
- The source planning document remains local only; repository notes are written separately.

## Test Status

No runtime test in this version.

## Next Step

Implement the minimal C++ `VectorIndex`, pybind11 binding, and a Python smoke test.
