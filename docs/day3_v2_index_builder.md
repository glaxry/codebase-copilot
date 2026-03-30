# Day 3 - Version 2: Index Builder and Metadata Persistence

## Goal

Connect embeddings, chunks, the C++ retriever, and `metadata.json` into one indexing pipeline.

## What This Version Contains

- batch add support in the C++ vector index and Python retriever
- `build_index()` for:
  - loading repository files
  - chunking source files
  - embedding chunk text
  - ingesting vectors into the retriever
  - writing `metadata.json`
- `IndexBuildResult` metadata for the build summary
- an index builder test that validates metadata persistence and retriever population

## Design Notes

- `metadata.json` is the stable Day 3 artifact that later stages can reuse
- embeddings are rebuilt on each run; they are not persisted yet
- the retriever is populated during index build so the full path is already wired for later retrieval work
- batch add keeps Python-to-C++ calls lower than adding every vector one by one

## Thought Process

- Day 3 is mainly about wiring the offline indexing path end to end
- persisting chunk metadata now is more important than persisting embeddings because the metadata is the source of later answer citations
- the local hashing embedder is enough to validate the indexing flow even before a heavier embedding backend is introduced

## Tests

Run:

```powershell
python scripts/build_extension.py
python test_binding.py
python test_index_builder.py
```

The tests verify native batch ingestion, successful metadata writing, and that the retriever size matches the number of indexed chunks.

## Next Step

Expose `build_index()` through `python python/main.py index --repo ...` and add an acceptance test that validates the actual command line workflow.
