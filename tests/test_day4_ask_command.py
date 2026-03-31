from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = ROOT / "python" / "main.py"
BUILD_SCRIPT = ROOT / "scripts" / "build_extension.py"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_demo_repo(repo_root: Path) -> None:
    _write_text(
        repo_root / "src" / "app.py",
        '"""Application entry point for the demo repository."""\n\n'
        "from config import load_runtime_config\n"
        "from auth_service import login_user\n\n"
        "def main():\n"
        "    config = load_runtime_config()\n"
        '    return login_user("demo", "secret", config)\n',
    )
    _write_text(
        repo_root / "src" / "auth_service.py",
        '"""Authentication service that validates username and password before issuing a token."""\n\n'
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    token_ttl = config["token_ttl"]\n'
        '    return f"{username}:{token_ttl}"\n',
    )
    _write_text(
        repo_root / "src" / "config.py",
        '"""Configuration loader for token settings."""\n\n'
        "import os\n\n"
        "def load_runtime_config() -> dict[str, str]:\n"
        "    return {\n"
        '        "environment": os.getenv("APP_ENV", "dev"),\n'
        '        "token_ttl": os.getenv("TOKEN_TTL", "3600"),\n'
        "    }\n",
    )
    _write_text(
        repo_root / "docs" / "entrypoint_notes.md",
        "# Entry Point Notes\n\n"
        "People often ask where the application entry point is.\n"
        "This note discusses the application entry point at a high level and references src/app.py.\n"
        "Use the source file itself as the ground truth instead of this document.\n",
    )


def run_day4_ask_command_test() -> list[str]:
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=ROOT, check=True)

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
                "20",
                "--overlap",
                "5",
                "--embedding-dim",
                "128",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        expectations = [
            ("Where is the application entry point?", "src/app.py"),
            ("Which file validates username and password?", "src/auth_service.py"),
            ("How is token configuration loaded?", "src/config.py"),
        ]

        validated_paths: list[str] = []
        for question, expected_path in expectations:
            completed = subprocess.run(
                [
                    sys.executable,
                str(MAIN_SCRIPT),
                "ask",
                question,
                "--index",
                str(metadata_path),
                "--answer-mode",
                "local",
                "--top-k",
                "3",
                "--preview-lines",
                    "2",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            assert "backend=local" in completed.stdout
            assert "answer=" in completed.stdout
            assert f"source path={expected_path}" in completed.stdout
            assert "sources=" in completed.stdout
            assert "source path=docs/entrypoint_notes.md" not in completed.stdout.splitlines()[3:6]
            validated_paths.append(expected_path)

        return validated_paths


def main() -> int:
    validated_paths = run_day4_ask_command_test()
    print("Day 4 ask command test passed.")
    for path in validated_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
