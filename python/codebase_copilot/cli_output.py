from __future__ import annotations

from pathlib import Path

from .models import AnswerResult, PatchSuggestionResult, RetrievedChunk


def _header(title: str) -> list[str]:
    return [f"=== {title} ==="]


def _render_sources(sources: list[RetrievedChunk], preview_lines: int) -> list[str]:
    lines = ["--- SOURCES ---", f"sources={len(sources)}"]

    for index, source in enumerate(sources, start=1):
        chunk = source.chunk
        lines.append(f"source_rank={index}")
        lines.append(
            f"source path={chunk.relative_path} lines={chunk.start_line}-{chunk.end_line} score={source.score:.6f}"
        )
        for line in chunk.text.splitlines()[: max(preview_lines, 0)]:
            lines.append(f"  {line}")

    return lines


def render_scan_output(file_count: int, preview_rows: list[str]) -> str:
    lines = _header("SCAN RESULT")
    lines.append(f"files={file_count}")
    if preview_rows:
        lines.append("--- FILE PREVIEW ---")
        lines.extend(preview_rows)
    return "\n".join(lines)


def render_chunk_output(
    file_count: int,
    chunk_count: int,
    preview_rows: list[str],
    output_path: Path | None,
) -> str:
    lines = _header("CHUNK RESULT")
    lines.append(f"files={file_count}")
    lines.append(f"chunks={chunk_count}")
    if preview_rows:
        lines.append("--- CHUNK PREVIEW ---")
        lines.extend(preview_rows)
    if output_path is not None:
        lines.append(f"output={output_path}")
    return "\n".join(lines)


def render_index_output(repo_root: str, file_count: int, chunk_count: int, retriever_size: int, metadata_path: Path) -> str:
    lines = _header("INDEX RESULT")
    lines.append(f"repo={repo_root}")
    lines.append(f"files={file_count}")
    lines.append(f"chunks={chunk_count}")
    lines.append(f"retriever_size={retriever_size}")
    lines.append(f"metadata={metadata_path}")
    return "\n".join(lines)


def render_answer_output(result: AnswerResult, preview_lines: int, show_prompt: bool) -> str:
    lines = _header("ASK RESULT")
    lines.append(f"question={result.query}")
    lines.append(f"backend={result.backend}")
    if result.notice:
        lines.append(f"notice={result.notice}")
    lines.append("answer=")
    lines.append(result.answer)
    lines.extend(_render_sources(result.sources, preview_lines))
    if show_prompt:
        lines.append("--- PROMPT ---")
        lines.append("prompt=")
        lines.append(result.prompt)
    return "\n".join(lines)


def render_patch_output(result: PatchSuggestionResult, preview_lines: int, show_prompt: bool) -> str:
    lines = _header("PATCH RESULT")
    lines.append(f"request={result.query}")
    lines.append(f"backend={result.backend}")
    if result.notice:
        lines.append(f"notice={result.notice}")
    lines.append("suggestion=")
    lines.append(result.suggestion)
    lines.extend(_render_sources(result.sources, preview_lines))
    if show_prompt:
        lines.append("--- PROMPT ---")
        lines.append("prompt=")
        lines.append(result.prompt)
    return "\n".join(lines)


def render_benchmark_output(
    dataset_sizes: list[int],
    dimension: int,
    query_count: int,
    top_k: int,
    table: str,
    output_path: Path | None,
) -> str:
    lines = _header("BENCHMARK RESULT")
    lines.append(f"sizes={','.join(str(size) for size in dataset_sizes)}")
    lines.append(f"dimension={dimension}")
    lines.append(f"query_count={query_count}")
    lines.append(f"top_k={top_k}")
    lines.append("--- TABLE ---")
    lines.append(table)
    if output_path is not None:
        lines.append(f"output={output_path}")
    return "\n".join(lines)
