# Day 5 - Version 1: Patch Prompt and Result Model

## Goal

Create the Day 5 prompt and result structures for patch suggestions before wiring them into the agent and CLI.

## What This Version Contains

- `PatchSuggestionResult` in `python/codebase_copilot/models.py`
- `format_patch_contexts(...)` and `build_patch_prompt(...)` in `python/codebase_copilot/prompt.py`
- package exports for the new Day 5 prompt helpers
- a focused test that validates the generated patch prompt content and context formatting

## Acceptance Result

The prompt-level test confirms that a patch request now produces:

- grounded file path and line range context
- explicit patch-oriented instructions
- a reusable prompt format for the Day 5 agent path

## Run Commands

```powershell
python test_day5_patch_prompt.py
```

## Thought Process

- Day 5 starts with prompt structure because both the local suggestion path and the LLM-backed path need the same grounded context format
- the result dataclass is added now so later versions can return patch suggestions without reworking the public shape again
- this version stays intentionally small so the first Day 5 commit is easy to validate and push on its own