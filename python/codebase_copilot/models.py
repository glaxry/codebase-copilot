from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoFile:
    relative_path: str
    absolute_path: str
    language: str
    content: str

    @property
    def line_count(self) -> int:
        return len(self.content.splitlines())


@dataclass(frozen=True)
class CodeChunk:
    chunk_id: int
    relative_path: str
    language: str
    start_line: int
    end_line: int
    text: str

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1

    def to_embedding_text(self) -> str:
        return (
            f"File: {self.relative_path}\n"
            f"Lines: {self.start_line}-{self.end_line}\n"
            f"Language: {self.language}\n\n"
            f"{self.text}"
        )
