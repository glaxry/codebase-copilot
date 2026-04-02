# Day 9 - Version 3: Embedding Comparison Experiment

## Goal

Produce a reproducible hashing-vs-semantic comparison instead of only claiming that semantic embeddings are better.

## What This Version Contains

- a new comparison module:
  - `python/codebase_copilot/embedding_comparison.py`
- a report generator script:
  - `scripts/generate_embedding_comparison.py`
- a checked-in markdown report target:
  - `docs/embedding_comparison.md`

## Experiment Design

- use a small synthetic codebase with five focused files
- query it with five natural-language questions that include synonym gaps
- compare top-1 retrieval under:
  - hashing
  - semantic
- record expected path, actual top-1 path, and hit counts

## Why This Design Works

- it is deterministic and easy to rerun
- it isolates the embedding layer while keeping the same C++ retriever underneath
- it demonstrates the exact semantic gap that hashing struggles with

## Tests

- `tests/test_day9_embedding_comparison.py`

## Run Commands

```powershell
python test_day9_embedding_comparison.py
python scripts/generate_embedding_comparison.py
```
