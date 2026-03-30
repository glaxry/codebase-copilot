from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from codebase_copilot.pipeline import build_index


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_index_builder_test() -> tuple[int, int]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        _write_text(repo_root / "src" / "app.py", "def main():\n    return 1\n" * 50)
        _write_text(repo_root / "src" / "helper.cpp", "int helper() { return 2; }\n" * 60)
        metadata_path = repo_root / "data" / "metadata.json"

        result = build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=40,
            chunk_overlap=10,
            embedding_dimension=128,
        )

        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert result.file_count == 2
        assert result.chunk_count > 0
        assert result.retriever_size == result.chunk_count
        assert result.embedding_dimension == 128
        assert payload["file_count"] == result.file_count
        assert payload["chunk_count"] == result.chunk_count
        assert payload["embedding"]["provider"] == "hashing"
        assert len(payload["chunks"]) == result.chunk_count

        return result.file_count, result.chunk_count


def main() -> int:
    file_count, chunk_count = run_index_builder_test()
    print("Index builder test passed.")
    print(f"files={file_count}")
    print(f"chunks={chunk_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
