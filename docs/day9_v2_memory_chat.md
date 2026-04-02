# Day 9 - Version 2: Memory and Basic Chat Command

## Goal

Add in-process conversation memory to the agent path and expose a minimal interactive chat loop for multi-turn demos.

## What This Version Contains

- `CodebaseQAAgent.conversation_history`
- `clear_history()` support
- recent-turn injection into the ReAct prompt and the best-effort summary prompt
- automatic conversation recording after each `agent_run(...)`
- a new `chat` subcommand in `python/main.py`
- chat commands supported in this version:
  - `/clear`
  - `exit`
  - `quit`

## Design Notes

- memory is intentionally process-local and does not write to disk
- only the `agent` path records memory in this week, which keeps `ask` and `patch` backward-compatible and stateless
- the `chat` loop is intentionally simple in this version; richer mode switching and UX polish can be added later without rewriting the memory core

## Tests

- `tests/test_day9_memory_chat.py`

## Run Commands

```powershell
python test_day9_memory_chat.py
```
