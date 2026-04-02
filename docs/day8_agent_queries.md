# Day 8 Agent Demo Queries

These queries are prepared for the Week 1 ReAct agent demo.

## 1-Step Tool Call

```powershell
python python/main.py agent "Which file validates username and password?" --index data/metadata.json --answer-mode local
```

Expected behavior:

- the agent uses `search_codebase(...)`
- the search result is specific enough, so it stops after one tool call

## 2-Step Tool Call

```powershell
python python/main.py agent "Where is the application entry point?" --index data/metadata.json --answer-mode local
```

Expected behavior:

- Step 1: `search_codebase(...)`
- Step 2: `read_file(...)`
- Final answer references the file that defines `main()`

## 3-Step Tool Call

```powershell
python python/main.py agent "List the Python files first, then find the ask command workflow and show the implementation." --index data/metadata.json --answer-mode local
```

Expected behavior:

- Step 1: `list_files(pattern="*.py")`
- Step 2: `search_codebase(...)`
- Step 3: `read_file(...)`
- Final answer summarizes the `ask` workflow with a grounded file reference
