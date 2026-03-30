# Day 2 - Version 2: Chunker and Metadata

## Goal

Turn loaded repository files into overlapping line-based chunks with stable metadata.

## What This Version Contains

- `CodeChunk` metadata model
- `CodeChunker` for line-window chunking
- sequential chunk id assignment across files
- helper formatting for future embedding and prompt building
- a runnable chunker test covering overlap and line ranges

## Design Notes

- chunking is line-based, not AST-based, because the project plan explicitly favors a simple one-week implementation
- the defaults use `chunk_size=120` and `chunk_overlap=30`, which stay inside the recommended Day 2 range
- each chunk stores:
  - `chunk_id`
  - `relative_path`
  - `language`
  - `start_line`
  - `end_line`
  - `text`

## Thought Process

- chunk metadata must be stable now because later retrieval and answer citation depend on it
- overlap is necessary so important logic near chunk boundaries is not lost
- `to_embedding_text()` prepares the project for later embedding and LLM usage without forcing Day 3 to redesign the data format

## Test

Run:

```powershell
python test_chunker.py
```

The test builds a synthetic 12-line source file and verifies chunk ids, overlap windows, line ranges, and embedding text formatting.

## Next Step

Connect `RepositoryLoader` and `CodeChunker` into a runnable Day 2 pipeline, then add an end-to-end acceptance test that produces hundreds of chunks from a generated repository.
