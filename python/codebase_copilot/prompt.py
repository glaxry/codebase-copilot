from __future__ import annotations

from .models import RetrievedChunk


def format_qa_contexts(sources: list[RetrievedChunk]) -> str:
    if not sources:
        return "No indexed code context was retrieved."

    blocks: list[str] = []
    for index, source in enumerate(sources, start=1):
        chunk = source.chunk
        blocks.append(
            "\n".join(
                [
                    f"[Context {index}]",
                    f"Path: {chunk.relative_path}",
                    f"Lines: {chunk.start_line}-{chunk.end_line}",
                    f"Language: {chunk.language}",
                    f"Score: {source.score:.4f}",
                    chunk.text,
                ]
            )
        )
    return "\n\n".join(blocks)


def build_qa_prompt(query: str, sources: list[RetrievedChunk]) -> str:
    return (
        "You are a codebase analysis assistant. Answer the question only with the retrieved code "
        "context.\n"
        "Requirements:\n"
        "- cite the most relevant files and line ranges\n"
        "- stay concrete and avoid unsupported claims\n"
        "- if the context is insufficient, say so clearly\n\n"
        f"Question:\n{query}\n\n"
        f"Code Context:\n{format_qa_contexts(sources)}\n"
    )