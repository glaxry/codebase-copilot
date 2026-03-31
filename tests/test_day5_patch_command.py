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
        repo_root / "src" / "auth_service.py",
        '"""Authentication service for the demo repository."""\n\n'
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    token_ttl = config["token_ttl"]\n'
        '    return f"{username}:{token_ttl}"\n',
    )
    _write_text(
        repo_root / "src" / "app.py",
        "from auth_service import login_user\n\n"
        "def main() -> str:\n"
        '    return login_user("demo", "secret", {"token_ttl": "3600"})\n',
    )
    _write_text(
        repo_root / "docs" / "login_patch_notes.md",
        "# Login Patch Notes\n\n"
        "This markdown file mentions login validation, but the source file is the real edit target.\n",
    )


def run_day5_patch_command_test() -> tuple[str, str]:
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
                "6",
                "--overlap",
                "4",
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
                "patch",
                "How should I add input validation to the login flow?",
                "--index",
                str(metadata_path),
                "--answer-mode",
                "local",
                "--top-k",
                "4",
                "--preview-lines",
                "2",
                "--show-prompt",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        assert "backend=local" in completed.stdout
        assert "suggestion=" in completed.stdout
        assert "Suggested file: src/auth_service.py" in completed.stdout
        assert "Patch sketch:" in completed.stdout
        assert "source path=src/auth_service.py" in completed.stdout
        assert "prompt=" in completed.stdout
        assert "Patch Request:" in completed.stdout
        assert "source path=docs/login_patch_notes.md" not in completed.stdout.splitlines()[0:10]

        return "local", "src/auth_service.py"


def main() -> int:
    backend, primary_path = run_day5_patch_command_test()
    print("Day 5 patch command test passed.")
    print(f"backend={backend}")
    print(f"primary_path={primary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
