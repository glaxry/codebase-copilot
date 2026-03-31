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


def format_patch_contexts(sources: list[RetrievedChunk]) -> str:
    return format_qa_contexts(sources)


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


def build_patch_prompt(query: str, sources: list[RetrievedChunk]) -> str:
    return (
        "You are a senior codebase assistant. Produce a grounded patch suggestion using only the "
        "retrieved code context.\n"
        "Requirements:\n"
        "- identify the file or function that should be updated\n"
        "- explain why the change is needed\n"
        "- provide a concise patch-style sketch or pseudo-diff\n"
        "- do not invent files or logic outside the retrieved context\n"
        "- if the context is insufficient, say so clearly\n\n"
        f"Patch Request:\n{query}\n\n"
        f"Code Context:\n{format_patch_contexts(sources)}\n"
    )