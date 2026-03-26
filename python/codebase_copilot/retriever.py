from __future__ import annotations

from typing import Iterable

import numpy as np


def _load_native_module():
    try:
        from . import _vector_index
    except ImportError as exc:
        raise RuntimeError(
            "The native extension is not built yet. Run `python scripts/build_extension.py` first."
        ) from exc
    return _vector_index


class VectorRetriever:
    """Small Python wrapper around the Day 1 pybind11 module."""

    def __init__(self) -> None:
        self._native = _load_native_module().VectorIndex()

    @staticmethod
    def _coerce_vector(vector: Iterable[float] | np.ndarray) -> np.ndarray:
        array = np.asarray(vector, dtype=np.float32)
        if array.ndim != 1:
            raise ValueError("vector must be one-dimensional")
        return np.ascontiguousarray(array)

    def add_item(self, item_id: int, vector: Iterable[float] | np.ndarray) -> None:
        self._native.add_item(int(item_id), self._coerce_vector(vector))

    def search(
        self,
        query: Iterable[float] | np.ndarray,
        top_k: int = 3,
    ) -> list[tuple[int, float]]:
        if top_k <= 0:
            return []
        results = self._native.search(self._coerce_vector(query), int(top_k))
        return [(int(item_id), float(score)) for item_id, score in results]

    @property
    def size(self) -> int:
        return int(self._native.size())

    @property
    def dimension(self) -> int:
        return int(self._native.dimension())
