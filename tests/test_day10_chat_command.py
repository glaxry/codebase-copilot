from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = ROOT / "python" / "main.py"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_demo_repo(repo_root: Path) -> None:
    _write_text(
        repo_root / "src" / "app.py",
        '"""Application entry point for the demo repository."""\n\n'
        "from auth_service import login_user\n\n"
        "def main() -> str:\n"
        '    return login_user("demo", "secret", {"token_ttl": "3600"})\n'
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
    )
    _write_text(
        repo_root / "src" / "auth_service.py",
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    return f"{username}:{config[\'token_ttl\']}"\n',
    )


def run_day10_chat_command_test() -> tuple[str, int]:
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
                "--top-k",
                "4",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            input=(
                "/help\n"
                "/history\n"
                "/mode ask\n"
                "Where is the application entry point?\n"
                "/mode patch\n"
                "How should I add input validation to the login flow?\n"
                "/mode nope\n"
                "/history\n"
                "/clear\n"
                "/history\n"
                "/mode agent\n"
                "What tools can you use?\n"
                "quit\n"
            ),
        )

        stdout = completed.stdout
        assert "Chat session started." in stdout
        assert "Chat commands:" in stdout
        assert "history_count=0" in stdout
        assert "mode switched to ask." in stdout
        assert "=== ASK RESULT ===" in stdout
        assert "mode switched to patch." in stdout
        assert "=== PATCH RESULT ===" in stdout
        assert "error=usage: /mode agent|ask|patch" in stdout
        assert "[1] mode=ask" in stdout
        assert "[2] mode=patch" in stdout
        assert "history cleared." in stdout
        assert stdout.count("history_count=0") >= 2
        assert "mode switched to agent." in stdout
        assert "=== AGENT RESULT ===" in stdout
        assert "No tool calls were needed." in stdout
        assert "I can search indexed code" in stdout
        assert "chat closed." in stdout

        return "agent", 2


def test_day10_chat_command() -> None:
    run_day10_chat_command_test()


def main() -> int:
    mode, history_entries = run_day10_chat_command_test()
    print("Day 10 chat command test passed.")
    print(f"mode={mode}")
    print(f"history_entries={history_entries}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
