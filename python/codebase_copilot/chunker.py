from __future__ import annotations

from .config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from .models import CodeChunk, RepoFile


class CodeChunker:
    """Split repository files into overlapping line-based chunks."""

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.step = chunk_size - chunk_overlap

    def chunk_file(self, repo_file: RepoFile, start_chunk_id: int = 0) -> list[CodeChunk]:
        lines = repo_file.content.splitlines()
        if not lines:
            return []

        chunks: list[CodeChunk] = []
        current_chunk_id = start_chunk_id

        for start_index in range(0, len(lines), self.step):
            end_index = min(start_index + self.chunk_size, len(lines))
            chunk_lines = lines[start_index:end_index]
            if not chunk_lines:
                continue

            chunks.append(
                CodeChunk(
                    chunk_id=current_chunk_id,
                    relative_path=repo_file.relative_path,
                    language=repo_file.language,
                    start_line=start_index + 1,
                    end_line=end_index,
                    text="\n".join(chunk_lines),
                )
            )
            current_chunk_id += 1

            if end_index >= len(lines):
                break

        return chunks

    def chunk_repository(self, repo_files: list[RepoFile], start_chunk_id: int = 0) -> list[CodeChunk]:
        all_chunks: list[CodeChunk] = []
        current_chunk_id = start_chunk_id

        for repo_file in repo_files:
            file_chunks = self.chunk_file(repo_file, current_chunk_id)
            all_chunks.extend(file_chunks)
            current_chunk_id += len(file_chunks)

        return all_chunks
