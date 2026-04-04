# Day 10 - Version 1: LLM Streaming Final Answers

## Goal

Add streaming support to the OpenAI-compatible backend so the ReAct agent can print the final answer incrementally instead of waiting for the full response body.

## Why This Version Exists

Week 3 starts with the user-facing latency problem in the agent flow:

- the agent already knew how to do multi-step tool use
- the final answer still waited for a full blocking completion
- interactive usage felt slow even when the model had already started producing tokens

This version adds a narrow streaming layer without breaking the existing non-streaming code path that earlier tests and batch commands already depend on.

## Design

### 1. Keep the existing blocking API

`OpenAICompatibleChatSynthesizer.generate()` is still preserved. This matters because:

- earlier Day 4 and Day 8 tests already assume a blocking request
- `ask` and `patch` still work well with regular completions
- mocked tests are simpler when a full response body can still be returned at once

### 2. Add a separate SSE iterator

`OpenAICompatibleChatSynthesizer.generate_stream()` now:

- sends `stream=true` in the OpenAI-compatible request payload
- reads `data: ...` lines from the HTTP response
- stops on `[DONE]`
- extracts token deltas from `choices[0].delta.content`
- raises `LLMRequestError` on malformed or failed responses

This keeps the transport logic in `llm.py` instead of leaking HTTP parsing into CLI code.

### 3. Stream only the user-facing final answer

The ReAct tool loop still uses blocking calls for intermediate reasoning steps.

That split is intentional:

- tool planning needs a fully parsed XML-style response with `<thought>`, `<tool_call>`, or `<final_answer>`
- only the last user-facing answer benefits from token streaming
- this reduces implementation complexity while still improving perceived responsiveness

### 4. Add terminal streaming utility

`cli_output.py` now includes `stream_to_terminal()`:

- writes streamed chunks directly to a target text stream
- flushes after every chunk
- returns the fully collected final text so the agent can still persist conversation memory

## Code Changes

### `python/codebase_copilot/llm.py`

- added `_build_payload(..., stream=True|False)`
- added `_build_request(...)`
- added `_extract_stream_chunk(...)`
- added `generate_stream(...)`

### `python/codebase_copilot/prompt.py`

- added `build_react_final_answer_prompt(...)`
- lets the agent ask the LLM to rewrite a draft `<final_answer>` into the final user-facing streamed answer

### `python/codebase_copilot/agent.py`

- `agent_run()` now accepts optional:
  - `step_callback`
  - `stream_handler`
- LLM-mode final answers can now be streamed after the tool loop finishes
- max-step best-effort summaries can also stream when the model never emitted `<final_answer>`

### `python/codebase_copilot/cli_output.py`

- added `stream_to_terminal(...)`
- `render_agent_output(...)` now supports `include_final_answer=False` so streaming and non-streaming paths can share formatting logic

### `python/main.py`

- added `--stream/--no-stream` to `agent`
- added `--stream/--no-stream` to `chat`
- wired the CLI to pass a terminal stream handler into `agent.agent_run(...)`

## Testing

New tests:

- `tests/test_day10_llm_streaming.py`
- `test_day10_llm_streaming.py`

Covered scenarios:

- SSE chunk parsing in `generate_stream()`
- terminal stream rendering in `stream_to_terminal()`
- ReAct final-answer streaming after a tool step
- regression coverage for earlier blocking `llm` and `agent` flows

## Validation Commands

```powershell
C:\Users\11212\.conda\envs\codebase\python.exe scripts\build_extension.py
C:\Users\11212\.conda\envs\codebase\python.exe test_day10_llm_streaming.py
C:\Users\11212\.conda\envs\codebase\python.exe test_day8_react_loop.py
C:\Users\11212\.conda\envs\codebase\python.exe test_day8_agent_tuning.py
C:\Users\11212\.conda\envs\codebase\python.exe test_day4_llm_backend.py
```

## Notes

- streaming currently targets the final answer stage, not every planner step
- this keeps Week 3 Version 1 focused and low-risk
- richer interactive chat commands and terminal polish are handled in the next versions
