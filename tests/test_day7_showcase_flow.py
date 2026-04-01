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
        "from auth_service import login_user\n"
        "from config import load_runtime_config\n\n"
        "def main() -> str:\n"
        "    config = load_runtime_config()\n"
        '    return login_user("demo", "secret", config)\n',
    )
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
        repo_root / "src" / "config.py",
        "def load_runtime_config() -> dict[str, str]:\n"
        '    return {"token_ttl": "3600"}\n',
    )
    _write_text(
        repo_root / "docs" / "notes.md",
        "# Demo Notes\n\n"
        "The source files remain the ground truth for ask and patch.\n",
    )


def run_day7_showcase_flow_test() -> tuple[str, str, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        benchmark_report = repo_root / "data" / "showcase_benchmark.md"
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
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "backend=local" in ask_result.stdout
        assert "src/app.py" in ask_result.stdout

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
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "backend=local" in patch_result.stdout
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
        assert "| Dataset | Python Avg (ms) | C++ Avg (ms) | Speedup | Top-K Match |" in benchmark_result.stdout
        assert benchmark_report.exists()

        return str(metadata_path), "src/app.py", str(benchmark_report)


def test_day7_showcase_flow() -> None:
    run_day7_showcase_flow_test()


def main() -> int:
    metadata_path, primary_path, benchmark_report = run_day7_showcase_flow_test()
    print("Day 7 showcase flow test passed.")
    print(f"metadata_path={metadata_path}")
    print(f"primary_path={primary_path}")
    print(f"benchmark_report={benchmark_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
