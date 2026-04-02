from __future__ import annotations

from typing import Iterable

import numpy as np

from .config import DEFAULT_SEMANTIC_EMBEDDING_MODEL


class SentenceTransformerEmbedder:
    """Sentence-transformers based semantic embedder with lazy dependency loading."""

    def __init__(self, model_name: str = DEFAULT_SEMANTIC_EMBEDDING_MODEL) -> None:
        if not model_name.strip():
            raise ValueError("model_name must be non-empty")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Semantic embedding requires `sentence-transformers`. "
                "Install it with `python -m pip install -r requirements.txt`."
            ) from exc

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self.dimension = int(self._model.get_sentence_embedding_dimension())

    def embed_text(self, text: str) -> np.ndarray:
        matrix = self.embed_texts([text])
        if matrix.size == 0:
            return np.empty((self.dimension,), dtype=np.float32)
        return matrix[0]

    def embed_texts(self, texts: Iterable[str]) -> np.ndarray:
        items = list(texts)
        if not items:
            return np.empty((0, self.dimension), dtype=np.float32)

        embeddings = self._model.encode(
            items,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        matrix = np.asarray(embeddings, dtype=np.float32)
        if matrix.ndim == 1:
            return matrix.reshape(1, -1)
        return matrix
