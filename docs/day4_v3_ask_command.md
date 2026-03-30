# Day 4 - Version 3: `ask` Command and CLI Acceptance

## Goal

Expose the Day 4 Q&A path through the real CLI and validate that the command itself can answer repository questions after indexing.

## What This Version Contains

- `python python/main.py ask "..." --index data/metadata.json`
- CLI flags for metadata path, `top-k`, source preview lines, and prompt debugging
- command output that prints the answer, retrieved source count, and source snippets
- a command-level acceptance test that builds the native extension, indexes a demo repo, and asks three real questions through the CLI

## Acceptance Result

The command-level test confirms that:

- the native extension is built first
- the repository is indexed through the existing `index` command
- `python python/main.py ask ...` exits successfully
- the answer output includes grounded source paths for each question

## Run Commands

```powershell
python scripts/build_extension.py
python python/main.py index --repo . --output data/metadata.json
python python/main.py ask "Where is the application entry point?" --index data/metadata.json --top-k 3
python test_day4_ask_command.py
```

## Thought Process

- the Day 4 acceptance criterion is about the end-to-end Q&A chain, so the final test executes the same CLI path a user would run
- the command prints both the synthesized answer and the retrieved sources so debugging stays easy before a richer interface exists
- prompt debugging is exposed through a flag because Day 5 patch suggestions will need the same inspectable context assembly pattern