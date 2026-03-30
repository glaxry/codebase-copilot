from __future__ import annotations

import json
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


def run_index_command_test() -> tuple[int, int]:
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=ROOT, check=True)

    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        _write_text(repo_root / "src" / "service.py", "def handle():\n    return 1\n" * 60)
        _write_text(repo_root / "src" / "util.cpp", "int util() { return 2; }\n" * 70)
        metadata_path = repo_root / "metadata.json"

        completed = subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "index",
                "--repo",
                str(repo_root),
                "--output",
                str(metadata_path),
                "--chunk-size",
                "40",
                "--overlap",
                "10",
                "--embedding-dim",
                "128",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert payload["file_count"] == 2
        assert payload["chunk_count"] > 0
        assert payload["embedding"]["dimension"] == 128
        assert "retriever_size=" in completed.stdout

        return payload["file_count"], payload["chunk_count"]


def main() -> int:
    file_count, chunk_count = run_index_command_test()
    print("Day 3 index command test passed.")
    print(f"files={file_count}")
    print(f"chunks={chunk_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
