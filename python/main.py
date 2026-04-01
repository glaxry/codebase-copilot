from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.benchmark import build_benchmark_report, format_benchmark_table, run_benchmark_suite
from codebase_copilot.cli_output import (
    render_answer_output,
    render_benchmark_output,
    render_chunk_output,
    render_index_output,
    render_patch_output,
    render_scan_output,
)
from codebase_copilot.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from codebase_copilot.llm import LLMRequestError, LLMSettings
from codebase_copilot.pipeline import build_chunks, build_index, load_repository, write_chunks_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codebase Copilot tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan a repository and list loadable files")
    scan_parser.add_argument("--repo", required=True, help="Repository path")
    scan_parser.add_argument("--preview", type=int, default=10, help="Number of files to preview")

    chunk_parser = subparsers.add_parser("chunk", help="Chunk a repository into line windows")
    chunk_parser.add_argument("--repo", required=True, help="Repository path")
    chunk_parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    chunk_parser.add_argument("--overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    chunk_parser.add_argument("--preview", type=int, default=5, help="Number of chunks to preview")
    chunk_parser.add_argument("--output", help="Optional path to write chunk metadata as JSON")

    index_parser = subparsers.add_parser("index", help="Build a Day 3 metadata index")
    index_parser.add_argument("--repo", required=True, help="Repository path")
    index_parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    index_parser.add_argument("--overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    index_parser.add_argument("--embedding-dim", type=int, default=256)
    index_parser.add_argument("--output", default="data/metadata.json", help="Path to write metadata JSON")

    ask_parser = subparsers.add_parser("ask", help="Ask a question against a Day 4 metadata index")
    ask_parser.add_argument("question", help="Question to ask about the indexed repository")
    ask_parser.add_argument("--index", default="data/metadata.json", help="Path to metadata JSON")
    ask_parser.add_argument("--top-k", type=int, default=4, help="Number of chunks to retrieve")
    ask_parser.add_argument(
        "--answer-mode",
        choices=("auto", "local", "llm"),
        default="auto",
        help="Choose local fallback, force llm, or automatically use llm when configured",
    )
    ask_parser.add_argument("--llm-model", help="Override the model name for OpenAI-compatible backends")
    ask_parser.add_argument("--llm-base-url", help="Override the OpenAI-compatible API base URL")
    ask_parser.add_argument("--llm-timeout", type=float, help="Override the LLM request timeout in seconds")
    ask_parser.add_argument(
        "--preview-lines",
        type=int,
        default=4,
        help="Number of source lines to print for each retrieved chunk",
    )
    ask_parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Print the assembled QA prompt for debugging",
    )

    patch_parser = subparsers.add_parser("patch", help="Ask for a grounded patch suggestion from a Day 5 metadata index")
    patch_parser.add_argument("question", help="Patch-style request about the indexed repository")
    patch_parser.add_argument("--index", default="data/metadata.json", help="Path to metadata JSON")
    patch_parser.add_argument("--top-k", type=int, default=4, help="Number of chunks to retrieve")
    patch_parser.add_argument(
        "--answer-mode",
        choices=("auto", "local", "llm"),
        default="auto",
        help="Choose local fallback, force llm, or automatically use llm when configured",
    )
    patch_parser.add_argument("--llm-model", help="Override the model name for OpenAI-compatible backends")
    patch_parser.add_argument("--llm-base-url", help="Override the OpenAI-compatible API base URL")
    patch_parser.add_argument("--llm-timeout", type=float, help="Override the LLM request timeout in seconds")
    patch_parser.add_argument(
        "--preview-lines",
        type=int,
        default=4,
        help="Number of source lines to print for each retrieved chunk",
    )
    patch_parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Print the assembled patch prompt for debugging",
    )

    benchmark_parser = subparsers.add_parser("benchmark", help="Run the Day 6 Python vs C++ retrieval benchmark")
    benchmark_parser.add_argument(
        "--sizes",
        default="1000,10000,50000,100000",
        help="Comma-separated dataset sizes to benchmark",
    )
    benchmark_parser.add_argument("--dimension", type=int, default=64, help="Synthetic vector dimension")
    benchmark_parser.add_argument("--query-count", type=int, default=20, help="Number of benchmark queries")
    benchmark_parser.add_argument("--top-k", type=int, default=5, help="Top-k results per query")
    benchmark_parser.add_argument("--seed", type=int, default=42, help="Random seed for synthetic data")
    benchmark_parser.add_argument(
        "--match-queries",
        type=int,
        default=5,
        help="Number of queries to reuse for Python/C++ top-k consistency checks",
    )
    benchmark_parser.add_argument(
        "--output",
        default="data/day6_benchmark.md",
        help="Optional markdown report path",
    )

    return parser


def _run_scan(args: argparse.Namespace) -> int:
    repo_files = load_repository(args.repo)
    preview_rows = [
        f"{repo_file.relative_path} [{repo_file.language}] lines={repo_file.line_count}"
        for repo_file in repo_files[: args.preview]
    ]
    print(render_scan_output(len(repo_files), preview_rows))
    return 0


def _run_chunk(args: argparse.Namespace) -> int:
    repo_files, chunks = build_chunks(args.repo, chunk_size=args.chunk_size, chunk_overlap=args.overlap)
    preview_rows = [
        f"chunk_id={chunk.chunk_id} path={chunk.relative_path} lines={chunk.start_line}-{chunk.end_line}"
        for chunk in chunks[: args.preview]
    ]

    output_path: Path | None = None
    if args.output:
        output_path = write_chunks_json(chunks, args.output)

    print(render_chunk_output(len(repo_files), len(chunks), preview_rows, output_path))
    return 0


def _run_index(args: argparse.Namespace) -> int:
    result = build_index(
        repo_root=args.repo,
        metadata_output=args.output,
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
        embedding_dimension=args.embedding_dim,
    )
    print(
        render_index_output(
            repo_root=args.repo,
            file_count=result.file_count,
            chunk_count=result.chunk_count,
            retriever_size=result.retriever_size,
            metadata_path=result.metadata_path,
        )
    )
    return 0


def _run_ask(args: argparse.Namespace) -> int:
    llm_settings = LLMSettings.from_env(
        base_url=args.llm_base_url,
        model=args.llm_model,
        timeout_seconds=args.llm_timeout,
    )
    agent = CodebaseQAAgent.from_metadata(args.index, llm_settings=llm_settings)

    try:
        result = agent.ask(args.question, top_k=args.top_k, answer_mode=args.answer_mode)
    except (LLMRequestError, ValueError) as exc:
        print(f"error={exc}", file=sys.stderr)
        return 2

    print(render_answer_output(result, preview_lines=args.preview_lines, show_prompt=args.show_prompt))

    return 0


def _run_patch(args: argparse.Namespace) -> int:
    llm_settings = LLMSettings.from_env(
        base_url=args.llm_base_url,
        model=args.llm_model,
        timeout_seconds=args.llm_timeout,
    )
    agent = CodebaseQAAgent.from_metadata(args.index, llm_settings=llm_settings)

    try:
        result = agent.patch(args.question, top_k=args.top_k, answer_mode=args.answer_mode)
    except (LLMRequestError, ValueError) as exc:
        print(f"error={exc}", file=sys.stderr)
        return 2

    print(render_patch_output(result, preview_lines=args.preview_lines, show_prompt=args.show_prompt))

    return 0


def _parse_benchmark_sizes(raw_sizes: str) -> list[int]:
    sizes: list[int] = []
    for part in raw_sizes.split(","):
        value = part.strip()
        if not value:
            continue
        size = int(value)
        if size <= 0:
            raise ValueError("benchmark sizes must be positive")
        sizes.append(size)
    if not sizes:
        raise ValueError("at least one benchmark size is required")
    return sizes


def _run_benchmark(args: argparse.Namespace) -> int:
    try:
        dataset_sizes = _parse_benchmark_sizes(args.sizes)
        results = run_benchmark_suite(
            dataset_sizes,
            dimension=args.dimension,
            query_count=args.query_count,
            top_k=args.top_k,
            seed=args.seed,
            match_query_limit=args.match_queries,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"error={exc}", file=sys.stderr)
        return 2

    table = format_benchmark_table(results)
    report = build_benchmark_report(results)

    output_path: Path | None = None
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")

    print(
        render_benchmark_output(
            dataset_sizes=dataset_sizes,
            dimension=args.dimension,
            query_count=args.query_count,
            top_k=args.top_k,
            table=table,
            output_path=output_path.resolve() if output_path is not None else None,
        )
    )

    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        return _run_scan(args)
    if args.command == "chunk":
        return _run_chunk(args)
    if args.command == "index":
        return _run_index(args)
    if args.command == "ask":
        return _run_ask(args)
    if args.command == "patch":
        return _run_patch(args)
    if args.command == "benchmark":
        return _run_benchmark(args)

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
