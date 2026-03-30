from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from codebase_copilot.retriever import VectorRetriever


def run_smoke_test() -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    retriever = VectorRetriever()

    dataset = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.95, 0.05, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )

    for item_id, vector in enumerate(dataset):
        retriever.add_item(item_id, vector)

    single_results = retriever.search(np.array([1.0, 0.0, 0.0], dtype=np.float32), top_k=2)

    batch_retriever = VectorRetriever()
    batch_retriever.add_items([10, 11, 12, 13], dataset)
    batch_results = batch_retriever.search(np.array([1.0, 0.0, 0.0], dtype=np.float32), top_k=2)

    assert retriever.size == 4
    assert retriever.dimension == 3
    assert [item_id for item_id, _ in single_results] == [0, 1]
    assert single_results[0][1] > single_results[1][1] > 0.0
    assert [item_id for item_id, _ in batch_results] == [10, 11]

    return single_results, batch_results


def test_binding_smoke() -> None:
    run_smoke_test()


def main() -> int:
    single_results, batch_results = run_smoke_test()
    print("Smoke test passed.")
    print("single_add_results=")
    for item_id, score in single_results:
        print(f"id={item_id}, score={score:.6f}")
    print("batch_add_results=")
    for item_id, score in batch_results:
        print(f"id={item_id}, score={score:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
