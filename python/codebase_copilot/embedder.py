from __future__ import annotations

import hashlib
import re
from typing import Iterable

import numpy as np

from .config import DEFAULT_EMBEDDING_PROVIDER, DEFAULT_SEMANTIC_EMBEDDING_MODEL


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\s]")


class HashingEmbedder:
    """A deterministic local embedder for the Day 3 indexing pipeline."""

    def __init__(self, dimension: int = 256) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = dimension

    @staticmethod
    def tokenize(text: str) -> list[str]:
        tokens = TOKEN_PATTERN.findall(text)
        return tokens or ["<empty>"]

    def embed_text(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype=np.float32)

        for token in self.tokenize(text):
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], byteorder="little") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = np.linalg.norm(vector)
        if norm == 0.0:
            return vector
        return vector / norm

    def embed_texts(self, texts: Iterable[str]) -> np.ndarray:
        rows = [self.embed_text(text) for text in texts]
        if not rows:
            return np.empty((0, self.dimension), dtype=np.float32)
        return np.vstack(rows).astype(np.float32)


def create_embedder(
    provider: str = DEFAULT_EMBEDDING_PROVIDER,
    *,
    dimension: int = 256,
    model_name: str | None = None,
) -> HashingEmbedder | "SentenceTransformerEmbedder":
    normalized_provider = provider.strip().lower()

    if normalized_provider == "hashing":
        return HashingEmbedder(dimension=dimension)

    if normalized_provider == "semantic":
        from .embedder_semantic import SentenceTransformerEmbedder

        resolved_model = (model_name or DEFAULT_SEMANTIC_EMBEDDING_MODEL).strip()
        return SentenceTransformerEmbedder(model_name=resolved_model)

    raise ValueError(f"Unsupported embedding provider: {provider}")
