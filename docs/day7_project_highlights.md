# Day 7 Project Highlights

## Project Positioning

`Codebase Copilot` is a local code-repository agent built for interview demos and resume presentation.

The project focuses on a complete engineering loop instead of a toy chat UI:

- index a real local repository
- retrieve grounded code chunks
- answer codebase questions
- generate patch-style suggestions
- benchmark Python versus C++ retrieval

## Why This Project Stands Out

### 1. It is code-oriented, not generic document RAG

- the indexed corpus is a real source tree
- retrieval is evaluated against file paths, code chunks, and line ranges
- the final output is grounded in repository structure instead of plain article text

### 2. It combines Python workflow with C++ performance work

- Python handles repository loading, chunking, prompting, CLI orchestration, and LLM integration
- C++ handles native vector storage and top-k cosine search
- `pybind11` bridges the two layers without introducing a separate service boundary

### 3. It has a measurable systems angle

- the project includes a Python brute-force baseline
- the benchmark suite measures the same retrieval workload against the C++ path
- the README contains a reproducible benchmark table instead of vague performance claims

## Technical Highlights

### Retrieval Layer

- native vector index implemented in `cpp/src/vector_index.cpp`
- `pybind11` binding exposed through `cpp/src/binding.cpp`
- query-time top-k retrieval reused by both `ask` and `patch`

### Agent Layer

- `python/codebase_copilot/agent.py` rebuilds the retriever from `metadata.json`
- the agent supports `local`, `llm`, and `auto` answer modes
- the patch flow reuses retrieval but applies a different prompt and local synthesizer

### CLI and Delivery Layer

- one entrypoint in `python/main.py`
- subcommands: `scan`, `chunk`, `index`, `ask`, `patch`, `benchmark`
- showcase-ready terminal output added in Day 7 for cleaner demos and screenshots

## Quantitative Result

The current benchmark in `README.md` and `data/day6_benchmark.md` shows that the native C++ retriever is materially faster than the Python brute-force baseline on synthetic vector workloads up to `100k` items.

## Demo Talking Points

If you need to explain the project quickly, emphasize these four points:

1. `Python` is responsible for the end-to-end Agent workflow.
2. `C++` is responsible for high-performance vector retrieval.
3. the system is grounded on real repository files and code chunks.
4. the benchmark provides a quantitative reason for the C++ layer to exist.
