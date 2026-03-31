# Day 6 - Version 2: Native Benchmark Comparison and Report Table

## Goal

Add the native C++ retriever to the Day 6 benchmark flow and generate a reusable markdown table for Python vs C++ performance comparisons.

## What This Version Contains

- native benchmark timing through the existing `VectorRetriever`
- Python vs C++ comparison for the same synthetic benchmark fixture
- top-k correctness checks between the Python baseline and the native retriever
- `run_benchmark_suite(...)` for multi-scale benchmark batches
- `format_benchmark_table(...)` for markdown-ready benchmark output
- tests that validate comparison results, correctness matching, and table formatting

## Acceptance Result

This version can now produce benchmark cases that include:

- Python average query latency
- C++ average query latency
- computed speedup
- top-k match verification between both implementations

It also emits a markdown table that can be dropped into README or saved by the CLI in the final Day 6 version.

## Run Commands

```powershell
python test_day6_python_benchmark.py
python test_day6_benchmark_comparison.py
```

## Thought Process

- correctness matching matters before discussing speedups, so the suite compares returned top-k ids before treating the result as trustworthy
- the benchmark table is generated in code instead of being handwritten, which avoids stale README numbers later
- the same benchmark fixture is reused for both engines so the comparison stays data-identical and reproducible
