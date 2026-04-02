from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Callable

from .models import RetrievedChunk
from .repo_loader import RepositoryLoader

DEFAULT_READ_FILE_MAX_LINES = 100
DEFAULT_TOOL_OBSERVATION_PREVIEW_LINES = 80


def format_search_results(sources: list[RetrievedChunk]) -> str:
    if not sources:
        return "No relevant indexed chunks were found."

    blocks: list[str] = []
    for source in sources:
        chunk = source.chunk
        blocks.append(
            "\n".join(
                [
                    f"[{chunk.relative_path} lines {chunk.start_line}-{chunk.end_line}]",
                    chunk.text,
                ]
            )
        )
    return "\n---\n".join(blocks)


def search_codebase(
    retrieve_fn: Callable[[str, int, str], list[RetrievedChunk]],
    query: str,
    top_k: int = 4,
) -> str:
    normalized_query = query.strip()
    if not normalized_query:
        return "error=search_codebase requires a non-empty query"
    if top_k <= 0:
        return "error=search_codebase requires top_k > 0"

    sources = retrieve_fn(normalized_query, top_k, "qa")
    return format_search_results(sources)


def truncate_tool_output(text: str, preview_lines: int = DEFAULT_TOOL_OBSERVATION_PREVIEW_LINES) -> str:
    if preview_lines < 0:
        return text

    lines = text.splitlines()
    if not lines:
        return text

    prefix: list[str] = []
    body = lines
    if lines[0].startswith("[") and lines[0].endswith("]"):
        prefix = [lines[0]]
        body = lines[1:]

    if len(body) <= preview_lines:
        return text

    truncated = prefix + body[:preview_lines]
    truncated.append(f"... ({len(body) - preview_lines} more lines omitted)")
    return "\n".join(truncated)


def _resolve_repo_path(repo_root: str | Path, relative_path: str) -> Path:
    root = Path(repo_root).resolve()
    candidate = (root / relative_path).resolve()
    candidate.relative_to(root)
    return candidate


def _read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\x00" in data:
        return None

    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def read_file(
    repo_root: str | Path,
    path: str,
    start_line: int | None = None,
    end_line: int | None = None,
    max_lines: int = DEFAULT_READ_FILE_MAX_LINES,
) -> str:
    normalized_path = path.strip()
    if not normalized_path:
        return "error=read_file requires a non-empty path"
    if max_lines <= 0:
        return "error=read_file requires max_lines > 0"

    try:
        target = _resolve_repo_path(repo_root, normalized_path)
    except ValueError:
        return f"error=path escapes repo root: {normalized_path}"

    if not target.exists() or not target.is_file():
        return f"error=file not found: {normalized_path}"

    content = _read_text(target)
    if content is None:
        return f"error=file is not a readable text file: {normalized_path}"

    lines = content.splitlines()
    if not lines:
        return f"[{normalized_path} lines 1-1]"

    first_line = max(start_line or 1, 1)
    last_line = min(end_line or len(lines), len(lines))
    if first_line > last_line:
        return f"error=invalid line range: {first_line}-{last_line}"

    bounded_last_line = min(last_line, first_line + max_lines - 1)
    selected = lines[first_line - 1 : bounded_last_line]
    block = "\n".join(selected)
    return f"[{normalized_path} lines {first_line}-{bounded_last_line}]\n{block}"


def list_files(repo_root: str | Path, pattern: str | None = None) -> str:
    loader = RepositoryLoader(repo_root)
    relative_paths = [path.relative_to(loader.repo_root).as_posix() for path in loader.iter_file_paths()]

    if pattern is not None and pattern.strip():
        relative_paths = [path for path in relative_paths if fnmatch(path, pattern.strip())]

    if not relative_paths:
        if pattern is not None and pattern.strip():
            return f"No files matched pattern: {pattern.strip()}"
        return "No supported files were found."

    return "\n".join(relative_paths)
