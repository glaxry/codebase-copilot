# Day 2 - Version 3: Runnable Pipeline and Acceptance

## Goal

Make Day 2 runnable end-to-end and verify the project can generate hundreds of chunks for a repository.

## What This Version Contains

- `python/main.py` with `scan` and `chunk` commands
- pipeline helpers for loading repos, chunking them, and writing JSON metadata
- an end-to-end acceptance test that generates a synthetic repository with 80 files
- JSON output support for later indexing work

## Acceptance Result

The generated repository test produces:

- `files=80`
- `chunks=320`

This satisfies the Day 2 requirement that a repository can produce hundreds of chunks.

## Run Commands

```powershell
python python/main.py scan --repo . --preview 10
python python/main.py chunk --repo . --preview 5 --output data/day2_chunks.json
python test_day2_pipeline.py
```

## Thought Process

- Day 2 is not finished until there is a command the user can actually run
- JSON output is included now because Day 3 will need a stable metadata representation anyway
- the acceptance test uses a generated repository so the result is deterministic and repeatable

## Notes

- the current repository may not itself yield hundreds of chunks yet, depending on its size
- the acceptance test proves the loader and chunker scale to that requirement when given a large enough repository
- `autumn_project1.md` is intentionally excluded from the loader so it does not pollute later indexing results
