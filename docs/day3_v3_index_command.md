# Day 3 - Version 3: `index` Command and CLI Acceptance

## Goal

Expose the Day 3 index build through a real command line entry point and validate that command directly.

## What This Version Contains

- `python python/main.py index --repo ...`
- CLI arguments for chunk size, overlap, embedding dimension, and metadata output path
- a command-level acceptance test that builds the native module and then runs the actual `index` command
- README updates for the new Day 3 workflow

## Acceptance Result

The command-level test confirms that:

- the native extension is built first
- `python python/main.py index --repo ...` exits successfully
- `metadata.json` is written
- the file count, chunk count, and retriever size are reported on stdout

## Run Commands

```powershell
python scripts/build_extension.py
python python/main.py index --repo . --output data/metadata.json
python test_day3_index_command.py
```

## Thought Process

- the Day 3 acceptance criterion is explicitly about the `index` command, so the test has to execute the real CLI, not only library calls
- chunking and embedding settings are exposed on the command line now so later tuning does not require code changes
- the CLI now mirrors the project roadmap more closely and sets up Day 4 for retrieval and question answering
