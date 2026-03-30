from __future__ import annotations

import json
from pathlib import Path

from .chunker import CodeChunker
from .models import CodeChunk, RepoFile
from .repo_loader import RepositoryLoader


def load_repository(repo_root: str | Path) -> list[RepoFile]:
    return RepositoryLoader(repo_root).load_files()


def build_chunks(
    repo_root: str | Path,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[list[RepoFile], list[CodeChunk]]:
    repo_files = load_repository(repo_root)
    chunker = CodeChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk_repository(repo_files)
    return repo_files, chunks


def serialize_chunks(chunks: list[CodeChunk]) -> list[dict[str, object]]:
    return [
        {
            "chunk_id": chunk.chunk_id,
            "path": chunk.relative_path,
            "language": chunk.language,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "text": chunk.text,
        }
        for chunk in chunks
    ]


def write_chunks_json(chunks: list[CodeChunk], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(serialize_chunks(chunks), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output
