from __future__ import annotations

import json
from pathlib import Path

from .chunker import CodeChunker
from .config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from .embedder import HashingEmbedder
from .models import CodeChunk, IndexBuildResult, RepoFile
from .repo_loader import RepositoryLoader
from .retriever import VectorRetriever


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
    return [chunk.to_record() for chunk in chunks]


def write_chunks_json(chunks: list[CodeChunk], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(serialize_chunks(chunks), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output


def build_index(
    repo_root: str | Path,
    metadata_output: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    embedding_dimension: int = 256,
) -> IndexBuildResult:
    repo_root_path = Path(repo_root).resolve()
    repo_files, chunks = build_chunks(repo_root_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    embedder = HashingEmbedder(dimension=embedding_dimension)
    embeddings = embedder.embed_texts([chunk.to_embedding_text() for chunk in chunks])

    retriever = VectorRetriever()
    if chunks:
        retriever.add_items([chunk.chunk_id for chunk in chunks], embeddings)

    metadata_path = Path(metadata_output)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "repo_root": str(repo_root_path),
        "embedding": {
            "provider": "hashing",
            "dimension": embedding_dimension,
        },
        "chunking": {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        "file_count": len(repo_files),
        "chunk_count": len(chunks),
        "chunks": serialize_chunks(chunks),
    }
    metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return IndexBuildResult(
        repo_root=str(repo_root_path),
        metadata_path=metadata_path,
        file_count=len(repo_files),
        chunk_count=len(chunks),
        embedding_dimension=embedding_dimension,
        retriever_size=retriever.size,
    )
