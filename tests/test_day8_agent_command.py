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


def run_day8_agent_command_test() -> tuple[str, int]:
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
                "agent",
                "Where is the application entry point?",
                "--index",
                str(metadata_path),
                "--answer-mode",
                "local",
                "--max-steps",
                "4",
                "--preview-lines",
                "4",
                "--show-prompt",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        assert "=== AGENT RESULT ===" in completed.stdout
        assert "backend=local" in completed.stdout
        assert "[Step 1] Thought:" in completed.stdout
        assert "[Step 1] Action: search_codebase(" in completed.stdout
        assert "[Step 2] Action: read_file(" in completed.stdout
        assert "[Final] Answer:" in completed.stdout
        assert "src/app.py" in completed.stdout
        assert "prompt=" in completed.stdout

        return "local", 2


def test_day8_agent_command() -> None:
    run_day8_agent_command_test()


def main() -> int:
    backend, expected_steps = run_day8_agent_command_test()
    print("Day 8 agent command test passed.")
    print(f"backend={backend}")
    print(f"expected_steps={expected_steps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
