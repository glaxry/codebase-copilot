# Day 8 - Version 3: Agent CLI, Step Logs, and Demo Queries

## Goal

Expose the new ReAct loop through the main CLI so the project can demonstrate a real agent workflow from the terminal.

## What This Version Contains

- a new `agent` subcommand in `python/main.py`
- CLI rendering for:
  - `=== AGENT RESULT ===`
  - `--- REACT TRACE ---`
  - `[Step N] Thought / Action / Observation`
  - `[Final] Answer`
- a dedicated command test:
  - `tests/test_day8_agent_command.py`
- prepared demo queries:
  - `docs/day8_agent_queries.md`

## Acceptance Result

The project can now run:

```powershell
python python/main.py agent "Where is the application entry point?" --index data/metadata.json --answer-mode local
```

That command prints a visible ReAct trace, shows the executed tools, and finishes with a grounded final answer.

## Run Commands

```powershell
python test_day8_agent_command.py
python test_day8_tool_dispatch.py
python test_day8_react_loop.py
python test_day8_no_tool.py
```
