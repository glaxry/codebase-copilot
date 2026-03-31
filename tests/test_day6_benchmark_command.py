from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = ROOT / "python" / "main.py"


def run_day6_benchmark_command_test() -> tuple[str, str]:
    with TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "benchmark_report.md"
        completed = subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "benchmark",
                "--sizes",
                "16,32",
                "--dimension",
                "8",
                "--query-count",
                "3",
                "--top-k",
                "2",
                "--match-queries",
                "2",
                "--output",
                str(output_path),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        assert "sizes=16,32" in completed.stdout
        assert "dimension=8" in completed.stdout
        assert "query_count=3" in completed.stdout
        assert "| Dataset | Python Avg (ms) | C++ Avg (ms) | Speedup | Top-K Match |" in completed.stdout
        assert "| 16 |" in completed.stdout
        assert "| 32 |" in completed.stdout
        assert "output=" in completed.stdout

        report = output_path.read_text(encoding="utf-8")
        assert "# Day 6 Benchmark" in report
        assert "- dataset sizes: 16, 32" in report
        assert "| Dataset | Python Avg (ms) | C++ Avg (ms) | Speedup | Top-K Match |" in report

        return "16,32", str(output_path)


def main() -> int:
    sizes, output_path = run_day6_benchmark_command_test()
    print("Day 6 benchmark command test passed.")
    print(f"sizes={sizes}")
    print(f"output_path={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
