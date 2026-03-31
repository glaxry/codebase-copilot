# Day 6 Benchmark

Synthetic random unit-vector retrieval benchmark.

- dataset sizes: 1,000, 10,000, 50,000, 100,000
- dimension: 64
- query_count: 20
- top_k: 5
- seed: 42

| Dataset | Python Avg (ms) | C++ Avg (ms) | Speedup | Top-K Match |
| ------: | --------------: | -----------: | ------: | :---------: |
| 1,000 | 10.939 | 0.034 | 324.13x | yes |
| 10,000 | 103.938 | 0.265 | 391.52x | yes |
| 50,000 | 648.134 | 3.697 | 175.31x | yes |
| 100,000 | 1230.405 | 6.051 | 203.34x | yes |
