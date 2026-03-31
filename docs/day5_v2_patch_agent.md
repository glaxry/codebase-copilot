# Day 5 - Version 2: Patch Suggestion Agent and Retrieval Optimization

## Goal

Turn the Day 5 patch prompt into a runnable patch-suggestion flow with both local and LLM-backed generation, while improving retrieval diversity for noisy or overlapping chunk sets.

## What This Version Contains

- `LocalPatchSynthesizer` in `python/codebase_copilot/agent.py`
- `CodebaseQAAgent.patch(...)` that mirrors the Day 4 `ask(...)` flow
- patch-mode support for `local`, `llm`, and `auto` execution paths
- retrieval deduplication for overlapping chunks from the same file
- a more diverse top-k selection pass that limits repeated chunks from one path before falling back
- focused tests that validate local patch output, mocked LLM patch output, and fallback behavior

## Acceptance Result

This version can now answer patch-style requests such as input validation or exception handling suggestions with:

- a primary target file
- a concrete change area
- a reasoned explanation
- a patch-style sketch grounded in retrieved code

The retrieval path also avoids flooding the prompt with near-duplicate overlapping chunks from the same file when chunk overlap is high.

## Run Commands

```powershell
python test_day5_patch_prompt.py
python test_day5_patch_agent.py
```

## Thought Process

- patch suggestion should reuse the same retrieval foundation as Q&A, so the implementation stays inside `CodebaseQAAgent` instead of branching into a separate pipeline
- chunk deduplication belongs in retrieval, because prompt-level fixes cannot recover context diversity after the wrong chunks were already selected
- the local patch suggester is intentionally deterministic and structured so the project remains usable even without an API key
- the LLM path reuses the existing OpenAI-compatible client to keep the external dependency surface small
