# Codebase Copilot

Codebase Copilot is a local code-repository Q&A agent built with Python and C++.

## Current Milestones

### Day 1

- pybind11 C++ retrieval core
- Python wrapper around the native vector index
- smoke test for native binding

### Day 2

- repository loader with filtering rules
- line-based chunker with overlap and metadata
- runnable pipeline commands for scan and chunk preview
- acceptance test that produces hundreds of chunks from a generated repository

### Day 3

- deterministic local hashing embedder
- index builder that connects chunk embeddings to the C++ retriever
- `metadata.json` output for indexed chunks
- runnable `index` command and command-level acceptance test

### Day 4

- metadata loader that rebuilds the in-memory retriever from Day 3 output
- grounded QA prompt assembly for retrieved code chunks
- deterministic local answer synthesizer with primary-source-first evidence selection
- optional OpenAI-compatible LLM backend with local fallback
- query-aware retrieval reranking that prefers source code and downweights `docs/*.md` for normal code questions
- runnable `ask` command and Day 4 acceptance tests for local, mocked LLM, and source-priority retrieval paths

## Environment Setup

```powershell
conda activate codebase
cd "D:\Autumn Campus Recruitmen\Codebase Copilot"
python -m pip install -r requirements.txt
```

## Day 1 Commands

```powershell
python scripts/build_extension.py
python test_binding.py
```

## Day 2 Commands

```powershell
python test_repo_loader.py
python test_chunker.py
python python/main.py scan --repo . --preview 10
python python/main.py chunk --repo . --preview 5 --output data/day2_chunks.json
python test_day2_pipeline.py
```

## Day 3 Commands

```powershell
python test_embedder.py
python test_index_builder.py
python python/main.py index --repo . --output data/metadata.json
python test_day3_index_command.py
```

## Day 4 Commands

```powershell
python test_day4_qa_pipeline.py
python python/main.py ask "Where is the application entry point?" --index data/metadata.json --top-k 3
python test_day4_ask_command.py
```

## Day 4 LLM Commands

```powershell
$env:CODEBASE_COPILOT_LLM_API_KEY="your-api-key"
python python/main.py ask "Where is the application entry point?" --index data/metadata.json --answer-mode llm --llm-model qwen3.5-122b-a10b
python test_day4_llm_backend.py
```

If your provider is not Alibaba Cloud DashScope, also set `CODEBASE_COPILOT_LLM_BASE_URL` or pass `--llm-base-url`.

## Version Notes

- `docs/day1_v1_project_scaffold.md`
- `docs/day1_v2_cpp_binding.md`
- `docs/day1_v3_validation.md`
- `docs/day1_v4_environment_update.md`
- `docs/day2_v1_repo_loader.md`
- `docs/day2_v2_chunker.md`
- `docs/day2_v3_pipeline_validation.md`
- `docs/day3_v1_embedder.md`
- `docs/day3_v2_index_builder.md`
- `docs/day3_v3_index_command.md`
- `docs/day4_v1_qa_prompt_search.md`
- `docs/day4_v2_local_answer_agent.md`
- `docs/day4_v3_ask_command.md`
- `docs/day4_v4_llm_backend.md`
- `docs/day4_v5_source_priority_rerank.md`

## Repository Rules

- `autumn_project1.md` is intentionally excluded from version control.
- `.vendor` is not required in the normal workflow.
- Each delivery version is accompanied by a matching note in `docs/`.