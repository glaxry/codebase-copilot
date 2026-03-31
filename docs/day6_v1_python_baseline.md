# Day 6 - Version 1: Python Brute-Force Benchmark Baseline

## Goal

Create the benchmark foundation for Day 6 by generating reproducible random vectors and measuring a Python-side brute-force retrieval baseline.

## What This Version Contains

- `python/codebase_copilot/benchmark.py` with reusable benchmark dataclasses
- deterministic random unit-vector generation for synthetic benchmark data
- `PythonBruteForceRetriever`, a reference cosine-similarity retriever implemented with Python loops
- a benchmark runner for Python-only search timing
- focused tests for determinism, retrieval correctness, and timing metadata

## Acceptance Result

This version establishes the Python baseline that Day 6 will compare against the native C++ retriever. The benchmark fixture is reproducible, the baseline search is correct, and the timing output is available for later report generation.

## Run Commands

```powershell
python test_day6_python_benchmark.py
```

## Thought Process

- the benchmark data must be reproducible, otherwise performance numbers are hard to compare across versions
- the Python baseline keeps the retrieval algorithm intentionally simple: full scan, cosine similarity, top-k maintenance
- vectors are still stored in a NumPy matrix to avoid exploding Python-object memory at larger dataset sizes, but scoring is done in Python loops so the baseline remains a true Python brute-force path
