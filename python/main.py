from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from codebase_copilot.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from codebase_copilot.pipeline import build_chunks, load_repository, write_chunks_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codebase Copilot Day 2 tools")
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


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        return _run_scan(args)
    if args.command == "chunk":
        return _run_chunk(args)

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
