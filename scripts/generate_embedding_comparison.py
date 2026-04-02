from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"

import sys

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from codebase_copilot.config import DEFAULT_SEMANTIC_EMBEDDING_MODEL
from codebase_copilot.embedding_comparison import write_embedding_comparison_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Week 2 embedding comparison markdown report")
    parser.add_argument(
        "--output",
        default=str(ROOT / "docs" / "embedding_comparison.md"),
        help="Markdown path to write",
    )
    parser.add_argument(
        "--semantic-model",
        default=DEFAULT_SEMANTIC_EMBEDDING_MODEL,
        help="Sentence-transformers model name",
    )
    args = parser.parse_args()

    output_path = write_embedding_comparison_report(args.output, semantic_model=args.semantic_model)
    print(f"output={output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
