from __future__ import annotations

from math import isclose

import numpy as np

from codebase_copilot.benchmark import (
    BenchmarkSpec,
    PythonBruteForceRetriever,
    create_benchmark_fixture,
    generate_random_unit_vectors,
    run_python_benchmark_case,
)


def run_day6_python_benchmark_test() -> tuple[int, float]:
    first = generate_random_unit_vectors(count=4, dimension=8, seed=7)
    second = generate_random_unit_vectors(count=4, dimension=8, seed=7)
    assert np.allclose(first, second)
    assert first.shape == (4, 8)
    assert np.allclose(np.linalg.norm(first, axis=1), np.ones(4, dtype=np.float32), atol=1e-5)

    dataset = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.8, 0.2, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    retriever = PythonBruteForceRetriever()
    retriever.add_items([10, 11, 12, 13], dataset)
    results = retriever.search(np.array([1.0, 0.0, 0.0], dtype=np.float32), top_k=2)
    assert [item_id for item_id, _ in results] == [10, 11]
    assert results[0][1] > results[1][1] > 0.0
    assert retriever.size == 4
    assert retriever.dimension == 3

    spec = BenchmarkSpec(dataset_size=32, dimension=16, query_count=5, top_k=3, seed=11)
    fixture = create_benchmark_fixture(spec)
    assert fixture.vectors.shape == (32, 16)
    assert fixture.queries.shape == (5, 16)

    case_result = run_python_benchmark_case(spec)
    assert case_result.spec == spec
    assert case_result.python_result.engine == "python"
    assert case_result.python_result.total_seconds >= 0.0
    assert case_result.python_result.average_ms >= 0.0
    assert case_result.cpp_result is None
    assert case_result.top_ids_match is None
    assert case_result.speedup is None
    assert isclose(
        case_result.python_result.average_ms,
        (case_result.python_result.total_seconds / spec.query_count) * 1000.0,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )

    return spec.dataset_size, case_result.python_result.average_ms


def test_day6_python_benchmark() -> None:
    run_day6_python_benchmark_test()


def main() -> int:
    dataset_size, average_ms = run_day6_python_benchmark_test()
    print("Day 6 python benchmark test passed.")
    print(f"dataset_size={dataset_size}")
    print(f"average_ms={average_ms:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
