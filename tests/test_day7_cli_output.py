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
        "from auth_service import login_user\n\n"
        "def main() -> str:\n"
        '    return login_user("demo", "secret", {"token_ttl": "3600"})\n',
    )
    _write_text(
        repo_root / "src" / "auth_service.py",
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    return f"{username}:{config[\'token_ttl\']}"\n',
    )


def run_day7_cli_output_test() -> tuple[str, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        benchmark_report = repo_root / "data" / "benchmark.md"
        _create_demo_repo(repo_root)

        index_result = subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "index",
                "--repo",
                str(repo_root),
                "--output",
                str(metadata_path),
                "--chunk-size",
                "8",
                "--overlap",
                "2",
                "--embedding-dim",
                "64",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "=== INDEX RESULT ===" in index_result.stdout
        assert "repo=" in index_result.stdout
        assert "metadata=" in index_result.stdout

        ask_result = subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "ask",
                "Where is the application entry point?",
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
        assert "=== ASK RESULT ===" in ask_result.stdout
        assert "question=Where is the application entry point?" in ask_result.stdout
        assert "--- SOURCES ---" in ask_result.stdout
        assert "backend=local" in ask_result.stdout
        assert "source_rank=1" in ask_result.stdout
        assert "source path=src/app.py" in ask_result.stdout

        patch_result = subprocess.run(
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
        assert "=== PATCH RESULT ===" in patch_result.stdout
        assert "request=How should I add input validation to the login flow?" in patch_result.stdout
        assert "--- SOURCES ---" in patch_result.stdout
        assert "--- PROMPT ---" in patch_result.stdout
        assert "suggestion=" in patch_result.stdout
        assert "Suggested file: src/auth_service.py" in patch_result.stdout

        benchmark_result = subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "benchmark",
                "--sizes",
                "16,32",
                "--dimension",
                "8",
                "--query-count",
                "3",
                "--top-k",
                "2",
                "--match-queries",
                "2",
                "--output",
                str(benchmark_report),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "=== BENCHMARK RESULT ===" in benchmark_result.stdout
        assert "--- TABLE ---" in benchmark_result.stdout
        assert "sizes=16,32" in benchmark_result.stdout
        assert "| Dataset | Python Avg (ms) | C++ Avg (ms) | Speedup | Top-K Match |" in benchmark_result.stdout
        assert "output=" in benchmark_result.stdout

        return str(metadata_path), str(benchmark_report)


def test_day7_cli_output() -> None:
    run_day7_cli_output_test()


def main() -> int:
    metadata_path, benchmark_report = run_day7_cli_output_test()
    print("Day 7 CLI output test passed.")
    print(f"metadata_path={metadata_path}")
    print(f"benchmark_report={benchmark_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
