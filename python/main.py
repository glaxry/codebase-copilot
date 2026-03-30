from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
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

    return parser


def _run_scan(args: argparse.Namespace) -> int:
    repo_files = load_repository(args.repo)
    print(f"files={len(repo_files)}")
    for repo_file in repo_files[: args.preview]:
        print(f"{repo_file.relative_path} [{repo_file.language}] lines={repo_file.line_count}")
    return 0


def _run_chunk(args: argparse.Namespace) -> int:
    repo_files, chunks = build_chunks(
        args.repo,
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
    )
    print(f"files={len(repo_files)}")
    print(f"chunks={len(chunks)}")

    for chunk in chunks[: args.preview]:
        print(
            f"chunk_id={chunk.chunk_id} path={chunk.relative_path} "
            f"lines={chunk.start_line}-{chunk.end_line}"
        )

    if args.output:
        output_path = write_chunks_json(chunks, args.output)
        print(f"output={output_path}")
    return 0


def _run_index(args: argparse.Namespace) -> int:
    result = build_index(
        repo_root=args.repo,
        metadata_output=args.output,
        chunk_size=args.chunk_size,
        chunk_overlap=args.overlap,
        embedding_dimension=args.embedding_dim,
    )
    print(f"files={result.file_count}")
    print(f"chunks={result.chunk_count}")
    print(f"retriever_size={result.retriever_size}")
    print(f"metadata={result.metadata_path}")
    return 0


def _run_ask(args: argparse.Namespace) -> int:
    agent = CodebaseQAAgent.from_metadata(args.index)
    result = agent.ask(args.question, top_k=args.top_k)

    print("answer=")
    print(result.answer)
    print(f"sources={len(result.sources)}")

    for source in result.sources:
        chunk = source.chunk
        print(
            f"source path={chunk.relative_path} "
            f"lines={chunk.start_line}-{chunk.end_line} score={source.score:.6f}"
        )
        for line in chunk.text.splitlines()[: max(args.preview_lines, 0)]:
            print(f"  {line}")

    if args.show_prompt:
        print("prompt=")
        print(result.prompt)

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

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())