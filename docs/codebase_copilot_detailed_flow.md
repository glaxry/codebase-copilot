# Codebase Copilot Detailed Flow

This file is generated from the repository code paths, primarily:

- `python/main.py`
- `python/codebase_copilot/pipeline.py`
- `python/codebase_copilot/repo_loader.py`
- `python/codebase_copilot/chunker.py`
- `python/codebase_copilot/embedder.py`
- `python/codebase_copilot/agent.py`
- `python/codebase_copilot/retriever.py`
- `python/codebase_copilot/llm.py`
- `python/codebase_copilot/prompt.py`
- `python/codebase_copilot/benchmark.py`
- `cpp/src/binding.cpp`
- `cpp/src/vector_index.cpp`

## Overview

```mermaid
flowchart TD
  U["User / CLI"] --> MAIN["python/main.py<br/>argparse subcommand router"]

  subgraph INGEST["Scan / Chunk / Index"]
    LR["RepositoryLoader.load_files()"]
    WALK["rglob('*') over repo"]
    SKIP["filter ignored dirs / names / suffixes / binaries"]
    READ["read_bytes()<br/>decode utf-8 / utf-8-sig / gb18030"]
    RF["RepoFile list"]
    CHUNKER["CodeChunker.chunk_repository()"]
    WINDOW["chunk_file()<br/>line windows with overlap<br/>step = chunk_size - overlap"]
    CC["CodeChunk list"]
    EMB["HashingEmbedder.embed_texts()<br/>chunk.to_embedding_text()"]
    VRADD["VectorRetriever.add_items()<br/>native _vector_index"]
    META["metadata.json<br/>repo_root / embedding / chunking / chunks"]
    LR --> WALK --> SKIP --> READ --> RF --> CHUNKER --> WINDOW --> CC --> EMB --> VRADD --> META
  end

  MAIN -->|scan| SCAN["scan"]
  SCAN --> LR
  SCAN --> SP["print file count and preview"]

  MAIN -->|chunk| CH["chunk"]
  CH --> LR
  CH --> CHUNKER
  CH --> WJSON["write_chunks_json() optional"]
  CH --> COUT["print chunk count and preview"]

  MAIN -->|index| IDX["index"]
  IDX --> LR
  IDX --> CHUNKER
  IDX --> EMB
  IDX --> VRADD
  IDX --> META
  IDX --> IOUT["print IndexBuildResult"]

  subgraph QA["ask / patch runtime"]
    SETTINGS["LLMSettings.from_env()"]
    FROMMETA["CodebaseQAAgent.from_metadata(index)"]
    LOADM["load_index_metadata()"]
    INIT["agent __init__()<br/>validate hashing provider<br/>init embedder / local synth / optional LLM synth / VectorRetriever"]
    REBUILD["rehydrate retriever in memory<br/>embed saved chunks again"]
    RET["retrieve(query, top_k, intent)"]
    QEMB["embed query"]
    SEARCH["VectorRetriever.search()<br/>candidate_count=min(size,max(top_k*24,128))"]
    RERANK["_rerank_score()<br/>similarity + path overlap + source/doc/test preference<br/>entrypoint / CLI / validation / logging / exception hints"]
    SELECT["_select_context_chunks()<br/>drop near-duplicates<br/>max 2 chunks per path<br/>defer docs/tests unless requested"]
    PROMPTQA["build_qa_prompt()"]
    PROMPTPATCH["build_patch_prompt()"]
    MODEQA{"answer_mode?"}
    MODEPATCH{"answer_mode?"}
    LOCALQA["LocalAnswerSynthesizer.generate()<br/>collect evidence lines and assemble answer"]
    LOCALPATCH["LocalPatchSynthesizer.generate()<br/>classify focus / find target line / build pseudo diff"]
    LLMQ["OpenAICompatibleChatSynthesizer.generate()<br/>POST /chat/completions"]
    LLMP["OpenAICompatibleChatSynthesizer.generate()<br/>POST /chat/completions"]
    FALLQA["LLM failed and mode is not forced llm"]
    FALLPATCH["LLM failed and mode is not forced llm"]
    ERR["raise to CLI -> print error and exit 2"]
    AQOUT["print answer / sources / optional prompt"]
    PQOUT["print suggestion / sources / optional prompt"]

    FROMMETA --> LOADM --> INIT --> REBUILD --> RET
    RET --> QEMB --> SEARCH --> RERANK --> SELECT
  end

  MAIN -->|ask| ASK["ask"]
  ASK --> SETTINGS
  ASK --> FROMMETA
  SELECT --> PROMPTQA --> MODEQA
  MODEQA -->|local| LOCALQA --> AQOUT
  MODEQA -->|llm or auto with settings| LLMQ
  LLMQ -->|success| AQOUT
  LLMQ -->|failure| FALLQA
  FALLQA --> LOCALQA
  FALLQA --> ERR

  MAIN -->|patch| PATCH["patch"]
  PATCH --> SETTINGS
  PATCH --> FROMMETA
  SELECT --> PROMPTPATCH --> MODEPATCH
  MODEPATCH -->|local| LOCALPATCH --> PQOUT
  MODEPATCH -->|llm or auto with settings| LLMP
  LLMP -->|success| PQOUT
  LLMP -->|failure| FALLPATCH
  FALLPATCH --> LOCALPATCH
  FALLPATCH --> ERR

  subgraph BENCH["benchmark"]
    SIZES["_parse_benchmark_sizes()"]
    SUITE["run_benchmark_suite()"]
    FIXTURE["create_benchmark_fixture()<br/>random unit vectors + queries"]
    PYBASE["PythonBruteForceRetriever<br/>Python loops cosine + min-heap top-k"]
    CPPBASE["VectorRetriever / C++ VectorIndex<br/>C++ scan + priority_queue top-k"]
    MATCH["compare_top_ids()"]
    TABLE["format_benchmark_table()"]
    REPORT["build_benchmark_report()"]
    WRITE["optional write data/day6_benchmark.md"]
    SIZES --> SUITE --> FIXTURE
    FIXTURE --> PYBASE
    FIXTURE --> CPPBASE
    FIXTURE --> MATCH
    PYBASE --> TABLE
    CPPBASE --> TABLE
    MATCH --> TABLE
    TABLE --> REPORT --> WRITE
  end

  MAIN -->|benchmark| B["benchmark"]
  B --> SIZES

  subgraph NATIVE["Native extension build and binding"]
    BUILD["scripts/build_extension.py"]
    CMAKE["locate cmake / pybind11"]
    CONF["cmake configure + build"]
    MOD["_vector_index module"]
    BIND["binding.cpp<br/>NumPy -> std::vector"]
    CORE["vector_index.cpp<br/>add_item(s) / search() / cosine / min-heap"]
    BUILD --> CMAKE --> CONF --> MOD --> BIND --> CORE
  end

  MOD -.loaded at runtime.-> VRADD
  MOD -.loaded at runtime.-> SEARCH
  MOD -.loaded at runtime.-> CPPBASE
```

## Ask / Patch Detail

```mermaid
flowchart TD
  CMD["ask or patch command"] --> META["load metadata JSON"]
  META --> CHUNKS["CodeChunk.from_record() rebuild chunk list"]
  CHUNKS --> AGENT["CodebaseQAAgent"]
  AGENT --> EMB["HashingEmbedder"]
  AGENT --> RETR["VectorRetriever"]
  AGENT --> MAP["chunk_id -> chunk map"]
  CHUNKS --> REEMB["embed loaded chunks again"]
  REEMB --> RETR

  AGENT --> RET["retrieve(query, top_k, intent)"]
  RET --> TERMS["extract query terms"]
  RET --> QV["embed query"]
  QV --> SEARCH["native vector search"]
  SEARCH --> CANDS["RetrievedChunk candidates"]
  CANDS --> RERANK["intent-aware rerank"]
  RERANK --> DEDUP["remove near duplicates"]
  DEDUP --> PICK["select final top-k context"]

  PICK --> QA_PROMPT["build_qa_prompt()"]
  PICK --> PATCH_PROMPT["build_patch_prompt()"]

  QA_PROMPT --> QA_MODE{"local or llm"}
  PATCH_PROMPT --> PATCH_MODE{"local or llm"}

  QA_MODE -->|local| LA["LocalAnswerSynthesizer"]
  QA_MODE -->|llm| LLM1["OpenAI-compatible chat request"]
  LLM1 -->|ok| QA_RES["AnswerResult backend=llm"]
  LLM1 -->|fail| QA_FB{"forced llm?"}
  QA_FB -->|no| LA
  QA_FB -->|yes| ERR1["raise error"]
  LA --> QA_RES2["AnswerResult backend=local"]

  PATCH_MODE -->|local| LP["LocalPatchSynthesizer"]
  PATCH_MODE -->|llm| LLM2["OpenAI-compatible chat request"]
  LLM2 -->|ok| PATCH_RES["PatchSuggestionResult backend=llm"]
  LLM2 -->|fail| PATCH_FB{"forced llm?"}
  PATCH_FB -->|no| LP
  PATCH_FB -->|yes| ERR2["raise error"]
  LP --> PATCH_RES2["PatchSuggestionResult backend=local"]
```

## Benchmark Detail

```mermaid
flowchart TD
  START["benchmark command"] --> PARSE["parse sizes"]
  PARSE --> SUITE["run_benchmark_suite()"]
  SUITE --> SPEC["BenchmarkSpec per dataset size"]
  SPEC --> FIX["create_benchmark_fixture()"]
  FIX --> DATA["dataset vectors"]
  FIX --> QUERIES["query vectors"]

  FIX --> PY["benchmark_python_search()"]
  FIX --> CPP["benchmark_cpp_search()"]
  FIX --> CMP["compare_top_ids()"]

  PY --> PYDET["PythonBruteForceRetriever<br/>store vectors + norms<br/>loop over all vectors per query<br/>manual cosine similarity<br/>min-heap top-k"]
  CPP --> CPPDET["VectorRetriever -> _vector_index<br/>binding.cpp converts NumPy arrays<br/>C++ VectorIndex scans entries<br/>cosine similarity<br/>priority_queue top-k"]

  PYDET --> TABLE["format_benchmark_table()"]
  CPPDET --> TABLE
  CMP --> TABLE
  TABLE --> REPORT["build_benchmark_report()"]
  REPORT --> OUT["optional markdown file"]
```