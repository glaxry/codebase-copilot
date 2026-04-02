from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

from codebase_copilot.embedding_comparison import (
    format_embedding_comparison_markdown,
    run_embedding_comparison,
)


class _FakeSentenceTransformer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def get_sentence_embedding_dimension(self) -> int:
        return 8

    def encode(
        self,
        items: list[str],
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> np.ndarray:
        rows: list[np.ndarray] = []
        for text in items:
            lowered = text.lower()
            vector = np.array(
                [
                    float(any(token in lowered for token in ("authenticate", "login", "sign in"))),
                    float(any(token in lowered for token in ("settings", "config", "runtime"))),
                    float(any(token in lowered for token in ("lookup", "search", "vector"))),
                    float(any(token in lowered for token in ("entry", "main", "boot"))),
                    float(any(token in lowered for token in ("access rights", "permission", "protected"))),
                    float("token" in lowered),
                    float("environment" in lowered),
                    1.0,
                ],
                dtype=np.float32,
            )
            norm = float(np.linalg.norm(vector))
            rows.append(vector if norm == 0.0 else vector / norm)
        return np.vstack(rows).astype(np.float32)


def _install_fake_sentence_transformers() -> None:
    fake_module = types.ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = _FakeSentenceTransformer
    sys.modules["sentence_transformers"] = fake_module


def run_day9_embedding_comparison_test() -> tuple[int, int]:
    _install_fake_sentence_transformers()

    rows = run_embedding_comparison(semantic_model="all-MiniLM-L6-v2")
    assert len(rows) == 5

    hashing_hits = sum(1 for row in rows if row.hashing_match)
    semantic_hits = sum(1 for row in rows if row.semantic_match)
    assert semantic_hits >= hashing_hits

    report = format_embedding_comparison_markdown(rows, semantic_model="all-MiniLM-L6-v2")
    assert "# Embedding Comparison" in report
    assert "| Query | Expected Top-1 | Hashing Top-1 | Semantic Top-1 |" in report
    assert "semantic top-1 hits" in report

    return hashing_hits, semantic_hits


def test_day9_embedding_comparison() -> None:
    run_day9_embedding_comparison_test()


def main() -> int:
    hashing_hits, semantic_hits = run_day9_embedding_comparison_test()
    print("Day 9 embedding comparison test passed.")
    print(f"hashing_hits={hashing_hits}")
    print(f"semantic_hits={semantic_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
