from __future__ import annotations

from codebase_copilot.chunker import CodeChunker
from codebase_copilot.models import RepoFile


def _make_repo_file(line_count: int) -> RepoFile:
    lines = [f"line {index}" for index in range(1, line_count + 1)]
    return RepoFile(
        relative_path="src/sample.py",
        absolute_path="D:/demo/src/sample.py",
        language="python",
        content="\n".join(lines),
    )


def run_chunker_test() -> list[tuple[int, int, int]]:
    repo_file = _make_repo_file(12)
    chunker = CodeChunker(chunk_size=5, chunk_overlap=2)
    chunks = chunker.chunk_file(repo_file, start_chunk_id=10)

    expected_ranges = [
        (10, 1, 5),
        (11, 4, 8),
        (12, 7, 11),
        (13, 10, 12),
    ]
    actual_ranges = [(chunk.chunk_id, chunk.start_line, chunk.end_line) for chunk in chunks]

    assert actual_ranges == expected_ranges
    assert chunks[0].relative_path == "src/sample.py"
    assert chunks[0].line_count == 5
    assert "File: src/sample.py" in chunks[0].to_embedding_text()
    assert "Lines: 1-5" in chunks[0].to_embedding_text()

    return actual_ranges


def main() -> int:
    ranges = run_chunker_test()
    print("Chunker test passed.")
    for chunk_id, start_line, end_line in ranges:
        print(f"chunk_id={chunk_id}, lines={start_line}-{end_line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
