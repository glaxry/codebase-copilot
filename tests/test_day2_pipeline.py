from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from codebase_copilot.pipeline import build_chunks, write_chunks_json


def _write_repo_file(path: Path, line_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"def generated_{index}():\n    return {index}\n"
        for index in range(line_count)
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_day2_pipeline_test() -> tuple[int, int]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "demo_repo"
        for file_index in range(80):
            _write_repo_file(repo_root / "src" / f"module_{file_index}.py", 40)

        repo_files, chunks = build_chunks(repo_root, chunk_size=40, chunk_overlap=10)
        output_path = write_chunks_json(chunks, repo_root / "chunks.json")

        assert len(repo_files) == 80
        assert len(chunks) >= 240
        assert output_path.exists()
        assert chunks[0].chunk_id == 0
        assert chunks[-1].chunk_id == len(chunks) - 1

        return len(repo_files), len(chunks)


def main() -> int:
    file_count, chunk_count = run_day2_pipeline_test()
    print("Day 2 pipeline test passed.")
    print(f"files={file_count}")
    print(f"chunks={chunk_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
