from __future__ import annotations

from codebase_copilot.benchmark import (
    BenchmarkSpec,
    compare_python_and_cpp,
    format_benchmark_table,
    run_benchmark_suite,
)


def run_day6_benchmark_comparison_test() -> tuple[int, str]:
    single_case = compare_python_and_cpp(
        BenchmarkSpec(dataset_size=64, dimension=16, query_count=4, top_k=3, seed=19)
    )
    assert single_case.python_result.engine == "python"
    assert single_case.cpp_result is not None
    assert single_case.cpp_result.engine == "cpp"
    assert single_case.top_ids_match is True
    assert single_case.speedup is not None
    assert single_case.speedup > 0.0

    suite = run_benchmark_suite(
        [32, 96],
        dimension=12,
        query_count=3,
        top_k=2,
        seed=23,
    )
    assert [case.spec.dataset_size for case in suite] == [32, 96]
    assert all(case.cpp_result is not None for case in suite)
    assert all(case.top_ids_match is True for case in suite)

    table = format_benchmark_table(suite)
    assert "| Dataset | Python Avg (ms) | C++ Avg (ms) | Speedup | Top-K Match |" in table
    assert "| 32 |" in table
    assert "| 96 |" in table
    assert "yes" in table
    assert "x" in table

    return len(suite), table.splitlines()[2]


def test_day6_benchmark_comparison() -> None:
    run_day6_benchmark_comparison_test()


def main() -> int:
    case_count, sample_row = run_day6_benchmark_comparison_test()
    print("Day 6 benchmark comparison test passed.")
    print(f"case_count={case_count}")
    print(f"sample_row={sample_row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
