from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from time import perf_counter
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class BenchmarkSpec:
    dataset_size: int
    dimension: int
    query_count: int
    top_k: int
    seed: int = 42


@dataclass(frozen=True)
class BenchmarkFixture:
    item_ids: list[int]
    vectors: np.ndarray
    queries: np.ndarray


@dataclass(frozen=True)
class BenchmarkRun:
    engine: str
    total_seconds: float
    average_ms: float


@dataclass(frozen=True)
class BenchmarkCaseResult:
    spec: BenchmarkSpec
    python_result: BenchmarkRun
    cpp_result: BenchmarkRun | None = None
    top_ids_match: bool | None = None

    @property
    def speedup(self) -> float | None:
        if self.cpp_result is None or self.cpp_result.average_ms <= 0.0:
            return None
        return self.python_result.average_ms / self.cpp_result.average_ms


def generate_random_unit_vectors(count: int, dimension: int, seed: int) -> np.ndarray:
    if count < 0:
        raise ValueError("count must be non-negative")
    if dimension <= 0:
        raise ValueError("dimension must be positive")

    rng = np.random.default_rng(seed)
    matrix = rng.normal(size=(count, dimension)).astype(np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


def create_benchmark_fixture(spec: BenchmarkSpec) -> BenchmarkFixture:
    vectors = generate_random_unit_vectors(spec.dataset_size, spec.dimension, seed=spec.seed)
    queries = generate_random_unit_vectors(spec.query_count, spec.dimension, seed=spec.seed + 1)
    return BenchmarkFixture(
        item_ids=list(range(spec.dataset_size)),
        vectors=vectors,
        queries=queries,
    )


class PythonBruteForceRetriever:
    """Reference brute-force retriever implemented with Python loops."""

    def __init__(self) -> None:
        self._item_ids: list[int] = []
        self._vectors = np.empty((0, 0), dtype=np.float32)
        self._norms: list[float] = []
        self._dimension = 0

    def add_items(
        self,
        item_ids: Iterable[int],
        vectors: Iterable[Iterable[float]] | np.ndarray,
    ) -> None:
        ids = [int(item_id) for item_id in item_ids]
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2:
            raise ValueError("vectors must be two-dimensional")
        if matrix.shape[0] != len(ids):
            raise ValueError("item_ids and vectors must have the same number of rows")

        if self._dimension == 0:
            self._dimension = int(matrix.shape[1])
        elif int(matrix.shape[1]) != self._dimension:
            raise ValueError("embedding dimension does not match existing index")

        self._item_ids = ids
        self._vectors = np.ascontiguousarray(matrix)
        self._norms = [self._compute_norm(row) for row in self._vectors]

    def search(
        self,
        query: Iterable[float] | np.ndarray,
        top_k: int = 3,
    ) -> list[tuple[int, float]]:
        if top_k <= 0 or not self._item_ids:
            return []

        query_array = np.asarray(query, dtype=np.float32)
        if query_array.ndim != 1:
            raise ValueError("query must be one-dimensional")
        if self._dimension == 0 or int(query_array.shape[0]) != self._dimension:
            raise ValueError("query dimension does not match index dimension")

        query_norm = self._compute_norm(query_array)
        if query_norm == 0.0:
            raise ValueError("query norm must be non-zero")

        query_values = [float(value) for value in query_array]
        best_items: list[tuple[float, int]] = []

        # The benchmark baseline stays intentionally simple: scan every vector,
        # compute cosine similarity in Python, and keep only the current top-k.
        for item_id, vector, vector_norm in zip(self._item_ids, self._vectors, self._norms, strict=True):
            dot_product = 0.0
            for query_value, vector_value in zip(query_values, vector, strict=True):
                dot_product += query_value * float(vector_value)

            score = dot_product / (query_norm * vector_norm)
            if len(best_items) < top_k:
                heapq.heappush(best_items, (score, item_id))
                continue
            if score > best_items[0][0]:
                heapq.heapreplace(best_items, (score, item_id))

        return [(item_id, score) for score, item_id in sorted(best_items, reverse=True)]

    @staticmethod
    def _compute_norm(vector: Iterable[float] | np.ndarray) -> float:
        squared_sum = 0.0
        for value in vector:
            scalar = float(value)
            squared_sum += scalar * scalar
        return math.sqrt(squared_sum)

    @property
    def size(self) -> int:
        return len(self._item_ids)

    @property
    def dimension(self) -> int:
        return self._dimension


def benchmark_python_search(fixture: BenchmarkFixture, top_k: int = 5) -> BenchmarkRun:
    retriever = PythonBruteForceRetriever()
    retriever.add_items(fixture.item_ids, fixture.vectors)

    start_time = perf_counter()
    for query in fixture.queries:
        retriever.search(query, top_k=top_k)
    total_seconds = perf_counter() - start_time
    average_ms = (total_seconds / max(len(fixture.queries), 1)) * 1000.0
    return BenchmarkRun(
        engine="python",
        total_seconds=total_seconds,
        average_ms=average_ms,
    )


def run_python_benchmark_case(spec: BenchmarkSpec) -> BenchmarkCaseResult:
    fixture = create_benchmark_fixture(spec)
    return BenchmarkCaseResult(
        spec=spec,
        python_result=benchmark_python_search(fixture, top_k=spec.top_k),
    )
