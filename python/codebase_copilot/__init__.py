"""Codebase Copilot Python package."""

from .chunker import CodeChunker
from .embedder import HashingEmbedder
from .models import CodeChunk, IndexBuildResult, RepoFile
from .pipeline import build_chunks, build_index, load_repository, serialize_chunks, write_chunks_json
from .repo_loader import RepositoryLoader
from .retriever import VectorRetriever

__all__ = [
    "CodeChunk",
    "CodeChunker",
    "HashingEmbedder",
    "IndexBuildResult",
    "RepoFile",
    "RepositoryLoader",
    "VectorRetriever",
    "build_chunks",
    "build_index",
    "load_repository",
    "serialize_chunks",
    "write_chunks_json",
]
