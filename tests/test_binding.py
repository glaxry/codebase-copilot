from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from codebase_copilot.retriever import VectorRetriever


def run_smoke_test() -> list[tuple[int, float]]:
    retriever = VectorRetriever()

    dataset = [
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.95, 0.05, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.0], dtype=np.float32),
    ]

    for item_id, vector in enumerate(dataset):
        retriever.add_item(item_id, vector)

    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    results = retriever.search(query, top_k=2)

    assert retriever.size == 4
    assert retriever.dimension == 3
    assert [item_id for item_id, _ in results] == [0, 1]
    assert results[0][1] > results[1][1] > 0.0

    return results


def test_binding_smoke() -> None:
    run_smoke_test()


def main() -> int:
    results = run_smoke_test()
    print("Smoke test passed.")
    for item_id, score in results:
        print(f"id={item_id}, score={score:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
