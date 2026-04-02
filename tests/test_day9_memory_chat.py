from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.pipeline import build_index


ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = ROOT / "python" / "main.py"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_demo_repo(repo_root: Path) -> None:
    _write_text(
        repo_root / "src" / "app.py",
        '"""Application entry point for the demo repository."""\n\n'
        "def main() -> str:\n"
        '    return "ok"\n'
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
    )
    _write_text(
        repo_root / "src" / "config.py",
        '"""Load runtime settings for the application."""\n\n'
        "def load_runtime_config() -> dict[str, str]:\n"
        '    return {"token_ttl": "3600"}\n',
    )


def run_day9_memory_history_test() -> tuple[int, int]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=12,
            chunk_overlap=3,
            embedding_dimension=128,
        )
        agent = CodebaseQAAgent.from_metadata(metadata_path)

        first = agent.agent_run("Where is the application entry point?", answer_mode="local", max_steps=4)
        assert len(agent.conversation_history) == 1

        second = agent.agent_run("How is configuration loaded?", answer_mode="local", max_steps=4)
        assert len(agent.conversation_history) == 2
        assert "Recent Conversation:" in second.prompt
        assert "[User]: Where is the application entry point?" in second.prompt
        assert "[Assistant]:" in second.prompt

        agent.clear_history()
        assert agent.conversation_history == []

        return len(first.steps), len(second.steps)


def run_day9_chat_command_test() -> tuple[str, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "index",
                "--repo",
                str(repo_root),
                "--output",
                str(metadata_path),
                "--chunk-size",
                "12",
                "--overlap",
                "3",
                "--embedding-dim",
                "128",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "chat",
                "--index",
                str(metadata_path),
                "--mode",
                "agent",
                "--answer-mode",
                "local",
                "--max-steps",
                "4",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            input="What tools can you use?\n/clear\nquit\n",
        )

        assert "Chat session started." in completed.stdout
        assert "=== AGENT RESULT ===" in completed.stdout
        assert "history cleared." in completed.stdout
        assert "chat closed." in completed.stdout

        return "agent", "history cleared."


def test_day9_memory_chat() -> None:
    run_day9_memory_history_test()
    run_day9_chat_command_test()


def main() -> int:
    first_steps, second_steps = run_day9_memory_history_test()
    mode, clear_message = run_day9_chat_command_test()
    print("Day 9 memory and chat test passed.")
    print(f"first_steps={first_steps}")
    print(f"second_steps={second_steps}")
    print(f"mode={mode}")
    print(clear_message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
