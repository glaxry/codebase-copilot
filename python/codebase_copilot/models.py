from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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

    def to_record(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "path": self.relative_path,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
        }

    @classmethod
    def from_record(cls, record: dict[str, object]) -> "CodeChunk":
        return cls(
            chunk_id=int(record["chunk_id"]),
            relative_path=str(record["path"]),
            language=str(record["language"]),
            start_line=int(record["start_line"]),
            end_line=int(record["end_line"]),
            text=str(record["text"]),
        )


@dataclass(frozen=True)
class IndexBuildResult:
    repo_root: str
    metadata_path: Path
    file_count: int
    chunk_count: int
    embedding_dimension: int
    retriever_size: int


@dataclass(frozen=True)
class LoadedIndex:
    repo_root: str
    metadata_path: Path
    embedding_provider: str
    embedding_dimension: int
    chunk_size: int
    chunk_overlap: int
    file_count: int
    chunk_count: int
    chunks: list[CodeChunk]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: CodeChunk
    score: float


@dataclass(frozen=True)
class AnswerResult:
    query: str
    answer: str
    prompt: str
    sources: list[RetrievedChunk]