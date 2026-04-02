from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.pipeline import build_index


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_demo_repo(repo_root: Path) -> None:
    _write_text(
        repo_root / "src" / "app.py",
        "def main() -> str:\n"
        '    return "ok"\n',
    )


def run_day8_no_tool_test() -> str:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=8,
            chunk_overlap=2,
            embedding_dimension=64,
        )

        agent = CodebaseQAAgent.from_metadata(metadata_path)
        result = agent.agent_run("What tools can you use?", answer_mode="local", max_steps=4)

        assert result.backend == "local"
        assert result.steps == []
        assert "search indexed code" in result.answer.lower()
        assert "read repository files" in result.answer.lower()

        return result.answer


def test_day8_no_tool() -> None:
    run_day8_no_tool_test()


def main() -> int:
    answer = run_day8_no_tool_test()
    print("Day 8 no-tool test passed.")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
