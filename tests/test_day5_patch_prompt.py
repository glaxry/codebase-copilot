from __future__ import annotations

from codebase_copilot.models import CodeChunk, RetrievedChunk
from codebase_copilot.prompt import build_patch_prompt, format_patch_contexts


def _make_sources() -> list[RetrievedChunk]:
    chunk = CodeChunk(
        chunk_id=1,
        relative_path="python/codebase_copilot/repo_loader.py",
        language="python",
        start_line=10,
        end_line=24,
        text="def load_files():\n    return []\n",
    )
    return [RetrievedChunk(chunk=chunk, score=0.75)]


def run_day5_patch_prompt_test() -> tuple[str, str]:
    sources = _make_sources()
    formatted_contexts = format_patch_contexts(sources)
    prompt = build_patch_prompt("How should I add parameter validation here?", sources)

    assert "Path: python/codebase_copilot/repo_loader.py" in formatted_contexts
    assert "Lines: 10-24" in formatted_contexts
    assert "Score: 0.7500" in formatted_contexts
    assert "How should I add parameter validation here?" in prompt
    assert "identify the file or function that should be updated" in prompt
    assert "provide a concise patch-style sketch or pseudo-diff" in prompt
    assert "repo_loader.py" in prompt

    return formatted_contexts, prompt


def test_day5_patch_prompt() -> None:
    run_day5_patch_prompt_test()


def main() -> int:
    formatted_contexts, prompt = run_day5_patch_prompt_test()
    print("Day 5 patch prompt test passed.")
    print(formatted_contexts)
    print(prompt.splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())