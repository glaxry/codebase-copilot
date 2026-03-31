"""Codebase Copilot Python package."""

from .agent import CodebaseQAAgent, LocalAnswerSynthesizer, LocalPatchSynthesizer, load_index_metadata
from .chunker import CodeChunker
from .embedder import HashingEmbedder
from .llm import LLMRequestError, LLMSettings, OpenAICompatibleChatSynthesizer
from .models import (
    AnswerResult,
    CodeChunk,
    IndexBuildResult,
    LoadedIndex,
    PatchSuggestionResult,
    RepoFile,
    RetrievedChunk,
)
from .pipeline import build_chunks, build_index, load_repository, serialize_chunks, write_chunks_json
from .prompt import build_patch_prompt, build_qa_prompt, format_patch_contexts, format_qa_contexts
from .repo_loader import RepositoryLoader
from .retriever import VectorRetriever

__all__ = [
    "AnswerResult",
    "build_patch_prompt",
    "build_qa_prompt",
    "CodeChunk",
    "CodebaseQAAgent",
    "CodeChunker",
    "format_patch_contexts",
    "format_qa_contexts",
    "HashingEmbedder",
    "IndexBuildResult",
    "LLMRequestError",
    "LLMSettings",
    "LoadedIndex",
    "LocalAnswerSynthesizer",
    "LocalPatchSynthesizer",
    "OpenAICompatibleChatSynthesizer",
    "PatchSuggestionResult",
    "RepoFile",
    "RepositoryLoader",
    "RetrievedChunk",
    "VectorRetriever",
    "build_chunks",
    "build_index",
    "load_index_metadata",
    "load_repository",
    "serialize_chunks",
    "write_chunks_json",
]
