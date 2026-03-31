# Day 5 - Version 3: Patch Command and CLI Acceptance

## Goal

Expose the Day 5 patch-suggestion flow through the main CLI so the project can be demoed with `index`, `ask`, and `patch` from one entry point.

## What This Version Contains

- a new `patch` subcommand in `python/main.py`
- CLI wiring for `--index`, `--top-k`, `--answer-mode`, `--llm-model`, `--llm-base-url`, `--llm-timeout`, `--preview-lines`, and `--show-prompt`
- command output that prints the backend, patch suggestion, retrieved sources, and optional prompt
- a command-level acceptance test that builds metadata and runs the new `patch` command end to end
- README updates for Day 5 milestones, commands, and version notes

## Acceptance Result

This version can now run:

```powershell
python python/main.py patch "How should I add input validation to the login flow?" --index data/metadata.json --answer-mode local
```

The command returns:

- the selected backend
- the grounded patch suggestion
- retrieved source chunks with preview lines
- the assembled patch prompt when `--show-prompt` is enabled

## Run Commands

```powershell
python test_day5_patch_prompt.py
python test_day5_patch_agent.py
python test_day5_patch_command.py
```

## Thought Process

- the `patch` command intentionally mirrors the Day 4 `ask` command so the CLI remains predictable
- command-level validation matters here because patch suggestions are only useful if users can reproduce them from the terminal during demos or interviews
- README is updated in this version, not earlier, so the final Day 5 command surface is documented once the workflow is stable
