# Day 2 - Version 1: Repository Loader

## Goal

Build the repository reading layer before chunking.

## What This Version Contains

- repository file model `RepoFile`
- shared Day 2 configuration for supported file types and ignored directories
- `RepositoryLoader` for recursive scanning and text loading
- a runnable test script for filtering and file loading behavior

## Design Notes

- the loader only accepts the file types defined in the original project plan: `.py`, `.cpp`, `.cc`, `.c`, `.h`, `.hpp`, `.md`
- ignored directories include the Day 2 required list: `.git`, `build`, `dist`, `node_modules`
- practical noise directories such as `__pycache__`, `.venv`, `.vendor`, `.vscode` are also filtered
- files containing NUL bytes are treated as binary and skipped

## Thought Process

- Day 2 should keep the repo ingestion path simple and deterministic
- filtering early avoids wasting later chunking and embedding work on garbage files
- storing `relative_path + language + content` is the minimum metadata needed for the next stage

## Test

Run:

```powershell
python test_repo_loader.py
```

The test creates a temporary repository, mixes supported files, ignored directories, and binary content, and verifies that only the expected source files are loaded.

## Next Step

Implement line-based chunking and metadata generation on top of `RepositoryLoader`.
