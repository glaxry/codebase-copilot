# Day 7 Sample Queries

This file collects concise showcase queries for the final demo flow.

## Ask Queries

- `Where is the application entry point?`
- `Which file validates username and password?`
- `How is token configuration loaded?`
- `Which file handles the ask command workflow?`
- `Where is the OpenAI-compatible chat request constructed?`

## Patch Queries

- `How should I add input validation to the login flow?`
- `How should I add exception handling to the login flow?`
- `How should I add logging around token generation?`
- `Which file should I update to add stricter config validation?`
- `How would you patch the CLI to surface more debug information?`

## Benchmark Commands

- `python python/main.py benchmark`
- `python python/main.py benchmark --sizes 1000,10000,50000,100000 --dimension 64 --query-count 20 --top-k 5`
- `python python/main.py benchmark --sizes 500,1000 --dimension 32 --query-count 10 --top-k 3 --output data/day7_demo_benchmark.md`

## Suggested Demo Order

1. `python python/main.py index --repo . --output data/metadata.json`
2. `python python/main.py ask "Where is the application entry point?" --index data/metadata.json --answer-mode local --top-k 3`
3. `python python/main.py patch "How should I add input validation to the login flow?" --index data/metadata.json --answer-mode local --top-k 4`
4. `python python/main.py benchmark --sizes 1000,10000 --dimension 64 --query-count 20 --top-k 5`
