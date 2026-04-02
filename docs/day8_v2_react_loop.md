# Day 8 - Version 2: ReAct Loop and Tool Dispatch

## Goal

Upgrade the project from a single-pass RAG call into a genuine agent path that can think, decide, call tools, observe results, and then stop with a grounded final answer.

## What This Version Contains

- new `AgentStep` and `AgentRunResult` models
- a new `CodebaseQAAgent.agent_run(...)` method
- a local deterministic ReAct planner for offline and testable execution
- strict tool dispatch through `execute_tool(...)`
- prompt support for XML-like ReAct blocks:
  - `<thought>...</thought>`
  - `<tool_call>...</tool_call>`
  - `<final_answer>...</final_answer>`
- new tests:
  - `tests/test_day8_react_loop.py`
  - `tests/test_day8_no_tool.py`

## Design Notes

- the ReAct parser is intentionally lightweight and does not depend on an external agent framework
- `execute_tool(...)` returns error strings for unknown tools instead of raising, which keeps the loop observable and debuggable
- the local planner exists so the agent path remains runnable without an API key while the LLM path is still verified through mocked responses
- existing `ask()` and `patch()` methods are left untouched, so the old workflows remain backward compatible

## Acceptance Result

This version proves that the codebase can now run an iterative Agent path rather than only a single retrieval-and-answer call.

## Run Commands

```powershell
python test_day8_react_loop.py
python test_day8_no_tool.py
```
