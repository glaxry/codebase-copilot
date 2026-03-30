# Day 4 - Version 5: Source-Priority Retrieval Reranking

## Goal

Make `ask` prefer real source files over `docs/*.md` when the question is about code behavior, entry points, or implementation details.

## What This Version Contains

- query-aware retrieval reranking inside `python/codebase_copilot/agent.py`
- a larger retrieval candidate pool before final `top-k` selection so source chunks are less likely to be lost behind documentation chunks
- path-aware weighting that:
  - boosts source directories such as `src/`, `python/`, `cpp/`, and `include/`
  - downweights `docs/*.md` unless the query explicitly asks for docs/readme/notes
  - keeps tests available for test-related questions while lightly penalizing them for normal code questions
- regression tests that add an intentionally noisy `docs/entrypoint_notes.md` and still require `src/app.py` to rank first

## Acceptance Result

The updated Day 4 tests confirm that:

- `Where is the application entry point?` now ranks the source file before the markdown note that repeats the same phrase
- local `ask` command output still prints grounded source paths
- existing Day 3 index behavior remains unchanged

## Run Commands

```powershell
python scripts/build_extension.py
python test_day3_index_command.py
python test_day4_qa_pipeline.py
python test_day4_ask_command.py
```

## Thought Process

- the original failure mode was not only the LLM answer but the retrieval context itself: documentation chunks were being selected ahead of code chunks
- fixing this at retrieval time is better than trying to patch the prompt because the model can only answer from the sources it sees
- the reranker stays query-aware so docs and tests can still win when the user explicitly asks for them