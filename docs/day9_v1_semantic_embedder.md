# Day 9 - Version 1: Semantic Embedding Provider

## Goal

Add a semantic embedding option without breaking the existing hashing-based index and query workflow.

## What This Version Contains

- a new `python/codebase_copilot/embedder_semantic.py`
- `SentenceTransformerEmbedder` with the same `embed_text(...)` and `embed_texts(...)` surface as the hashing embedder
- `create_embedder(...)` factory support for:
  - `hashing`
  - `semantic`
- `index` command support for:
  - `--embedding-provider`
  - `--embedding-model`
- metadata persistence now records:
  - embedding provider
  - resolved embedding dimension
  - semantic model name when used
- backward-compatible metadata loading for old hashing indexes

## Compatibility Notes

- existing hashing indexes still load without rebuild
- old `ask`, `patch`, and `agent` flows keep working because the provider is read from `metadata.json`
- semantic dependencies are lazy-loaded, so the project still imports cleanly on machines that only use hashing

## Tests

- `tests/test_day9_semantic_embedder.py`

## Run Commands

```powershell
python test_day9_semantic_embedder.py
```
