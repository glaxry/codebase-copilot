"""Codebase Copilot Python package."""

from .chunker import CodeChunker
from .models import CodeChunk, RepoFile
from .pipeline import build_chunks, load_repository, serialize_chunks, write_chunks_json
from .repo_loader import RepositoryLoader
from .retriever import VectorRetriever

__all__ = [
    "CodeChunk",
    "CodeChunker",
    "RepoFile",
    "RepositoryLoader",
    "VectorRetriever",
    "build_chunks",
    "load_repository",
    "serialize_chunks",
    "write_chunks_json",
]
