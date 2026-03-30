# Day 4 - Version 4: OpenAI-Compatible LLM Backend

## Goal

Replace the Day 4 hardcoded offline-only answer path with a configurable LLM-backed path while keeping the local answerer as a safe fallback.

## What This Version Contains

- `python/codebase_copilot/llm.py` adds a minimal OpenAI-compatible chat client
- `python/codebase_copilot/config.py` now includes Day 4 LLM defaults for base URL, model, timeout, and token limits
- `python/codebase_copilot/agent.py` can now answer in `local`, `llm`, or `auto` mode
- `python/main.py ask` now supports `--answer-mode`, `--llm-model`, `--llm-base-url`, and `--llm-timeout`
- a mocked LLM backend test validates the request payload and the fallback path without requiring network access

## Configuration

Environment variables supported by the Day 4 LLM path:

- `CODEBASE_COPILOT_LLM_API_KEY` or `OPENAI_API_KEY`
- `CODEBASE_COPILOT_LLM_BASE_URL` or `OPENAI_BASE_URL`
- `CODEBASE_COPILOT_LLM_MODEL` or `OPENAI_MODEL`
- `CODEBASE_COPILOT_LLM_TIMEOUT_SECONDS`

Current defaults are:

- model: `qwen3.5-122b-a10b`
- base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`

## Acceptance Result

The Day 4 LLM test confirms that:

- the prompt is sent to `/chat/completions` in OpenAI-compatible format
- the configured model name is passed through correctly
- strict `llm` mode raises on request errors
- `auto` mode falls back to the local answerer when the LLM request fails

## Run Commands

```powershell
python scripts/build_extension.py
$env:CODEBASE_COPILOT_LLM_API_KEY="your-api-key"
python python/main.py ask "Where is the application entry point?" --index data/metadata.json --answer-mode llm --llm-model qwen3.5-122b-a10b
python test_day4_llm_backend.py
```

## Thought Process

- the API key is intentionally not stored in code, tests, or markdown so the repository stays safe to push
- the OpenAI-compatible request format keeps the project flexible across DashScope and other compatible providers
- fallback behavior matters because Day 4 should remain runnable in offline or restricted environments instead of failing completely