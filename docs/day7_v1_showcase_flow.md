# Day 7 - Version 1: Showcase Queries and End-to-End Demo Flow

## Goal

Turn the existing commands into a clean interview/demo path by adding sample queries, a reproducible showcase script, and a command-level smoke test that validates the final project loop.

## What This Version Contains

- `docs/day7_sample_queries.md` with showcase-ready `ask`, `patch`, and `benchmark` examples
- `scripts/day7_showcase_commands.ps1` for a step-by-step terminal demo on Windows
- `tests/test_day7_showcase_flow.py` to validate `index -> ask -> patch -> benchmark`
- a root wrapper `test_day7_showcase_flow.py` for direct execution

## Acceptance Result

This version proves that the final demo chain can be run in one pass:

- build metadata with `index`
- answer a grounded question with `ask`
- generate a grounded patch suggestion with `patch`
- print a benchmark table with `benchmark`

## Run Commands

```powershell
python test_day7_showcase_flow.py
powershell -ExecutionPolicy Bypass -File scripts/day7_showcase_commands.ps1
```

## Thought Process

- Day 7 is about presentation readiness, so the first version focuses on repeatability rather than new core logic
- the showcase script stays explicit and linear, which is better for interviews than hiding the workflow behind a new abstraction
- the smoke test mirrors the recommended demo order so the acceptance check and the user-facing story stay aligned
