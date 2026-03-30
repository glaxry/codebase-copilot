# Day 4 - Version 1: QA Retrieval and Prompt Assembly

## Goal

Turn the Day 3 metadata output into a reusable Day 4 question-answering input by loading chunks back, rebuilding retrieval, and assembling a grounded QA prompt.

## What This Version Contains

- `python/codebase_copilot/agent.py` now loads `metadata.json` and rebuilds the in-memory retriever from chunk text
- `python/codebase_copilot/models.py` now includes `LoadedIndex`, `RetrievedChunk`, and `AnswerResult`
- `python/codebase_copilot/prompt.py` builds a QA prompt from retrieved chunks with file paths, line ranges, languages, and similarity scores
- a Day 4 pipeline test that validates retrieval on a small synthetic repository

## Acceptance Result

The pipeline-level test confirms that a small demo repository can answer four grounded questions with the expected primary source file:

- application entry point
- username/password validation
- token configuration loading
- token issuing logic

## Run Commands

```powershell
python scripts/build_extension.py
python test_day4_qa_pipeline.py
```

## Thought Process

- Day 3 writes chunk metadata but not persisted embeddings, so Day 4 rebuilds the native retriever in memory when metadata is loaded
- prompt construction is separated into its own module so a future LLM backend can reuse the same grounded context format
- the first Day 4 acceptance point is retrieval quality, so the test checks that each question routes to the correct file before focusing on CLI formatting