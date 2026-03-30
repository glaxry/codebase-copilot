# Day 4 - Version 2: Local Answer Agent

## Goal

Make Day 4 runnable without any external service by adding a deterministic answer layer on top of the retrieved code chunks.

## What This Version Contains

- `LocalAnswerSynthesizer` for offline answers built directly from retrieved code lines
- `CodebaseQAAgent.ask(...)` that returns the prompt, answer text, and retrieved source chunks together
- evidence selection that prefers lines from the strongest matching chunk first and only then adds supporting context from other chunks
- prompt and answer outputs that stay grounded in file paths and line ranges

## Acceptance Result

The Day 4 QA pipeline now returns answers that include:

- the strongest matching file and line range
- relevant code lines or comments from that primary chunk
- additional supporting source references when multiple chunks are retrieved

## Run Commands

```powershell
python scripts/build_extension.py
python test_day4_qa_pipeline.py
```

## Thought Process

- a local deterministic answerer keeps the repository fully runnable in an offline environment and makes command-level testing practical
- the answerer is deliberately isolated from retrieval so a real LLM backend can replace it later without changing the indexing flow
- primary-source-first line selection keeps answers easier to read and avoids over-mixing unrelated chunks in the final response