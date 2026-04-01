# Day 7 Interview Talk

## 30-Second Version

`Codebase Copilot` is a local code-repository Agent built with Python and C++.

Python handles repository scanning, chunking, prompt construction, CLI orchestration, and optional LLM calls. C++ handles the native vector retrieval layer. I used `pybind11` to bridge the two sides. The project supports `index`, `ask`, `patch`, and `benchmark`, so I can both demo the workflow and show a measurable Python-vs-C++ retrieval comparison.

## 1-Minute Version

I wanted to build something closer to a real engineering workflow than a generic document chatbot, so I made a local codebase Agent.

The offline stage scans a repository, chunks the files, generates embeddings, and writes `metadata.json`. The online stage rebuilds the retriever in memory, embeds the user query, runs top-k retrieval through a native C++ index, then lets Python assemble a grounded answer or a patch suggestion. The CLI exposes the whole loop through `index`, `ask`, `patch`, and `benchmark`.

The main reason I used Python plus C++ is role separation: Python is efficient for orchestration and model integration, while C++ is better for performance-sensitive vector search. I also added a benchmark suite so the C++ layer is justified by numbers instead of architecture aesthetics.

## 3-Minute Version

The project goal was to build an interview-ready Agent for local repositories rather than a toy RAG demo.

The first part is the offline indexing pipeline. The system scans a local repo, filters files, chunks code into line windows with overlap, generates embeddings, and stores metadata such as file path, line range, language, and chunk text. The native retriever stores the vector side, while metadata stays in JSON so the project remains simple and easy to inspect.

The second part is the online runtime. When the user runs `ask`, the system loads `metadata.json`, rebuilds the retriever in memory, embeds the query, retrieves candidate chunks, reranks them to prefer source files over docs, and then builds a grounded prompt. For `patch`, the flow is similar, but the final prompt and local synthesizer are optimized for edit suggestions rather than explanation. I deliberately kept patching in suggestion mode instead of auto-edit mode, because that gives a safer MVP with clearer acceptance criteria.

The third part is the systems angle. I implemented a Python brute-force retrieval baseline and compared it with the C++ retriever on synthetic workloads. That benchmark makes the project stronger in interviews because I can explain not only what the system does, but also why the C++ layer exists and how much it helps.

## Likely Interview Questions

### Why not use FAISS directly?

Because the goal of this project was to demonstrate cross-language engineering and low-level retrieval implementation, not just assemble existing components. A hand-built brute-force retriever is also easier to finish within a short delivery schedule.

### Why stop at brute-force search instead of HNSW?

Because the one-week scope favored a complete and testable closed loop. Brute-force search was enough to validate the pipeline, support benchmark comparisons, and leave room for future ANN upgrades.

### Why does retrieval improve answer quality?

Because a repository is too large to hand to the model directly. Retrieval narrows the context to relevant code chunks, which reduces hallucination and improves grounding.

### Why does patch mode generate suggestions instead of editing files automatically?

Because suggestion mode is much easier to verify in a short project. It still demonstrates context understanding and engineering reasoning without adding risky file mutation logic.

## Live Demo Order

1. Run `index` to show repository ingestion.
2. Run `ask` to show grounded explanation.
3. Run `patch` to show targeted edit suggestions.
4. Run `benchmark` to show the quantitative result.
