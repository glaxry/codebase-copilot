from __future__ import annotations

import json

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


def format_react_history(history_blocks: list[str]) -> str:
    if not history_blocks:
        return "No previous tool observations yet."
    return "\n\n".join(history_blocks)


def build_react_prompt(
    query: str,
    history_blocks: list[str],
    max_steps: int,
) -> str:
    example_search = json.dumps(
        {
            "name": "search_codebase",
            "arguments": {"query": "application entry point main function", "top_k": 3},
        },
        ensure_ascii=False,
    )
    example_read = json.dumps(
        {
            "name": "read_file",
            "arguments": {"path": "python/main.py", "start_line": 141, "end_line": 170},
        },
        ensure_ascii=False,
    )
    example_list = json.dumps(
        {
            "name": "list_files",
            "arguments": {"pattern": "*.py"},
        },
        ensure_ascii=False,
    )
    return (
        "You are Codebase Copilot running a ReAct-style code investigation loop.\n"
        "You may think, call one tool, observe the tool result, and then continue until you can "
        "answer the user.\n\n"
        "Available tools:\n"
        "1. search_codebase(query: str, top_k: int = 4)\n"
        "   Use this to retrieve the most relevant indexed code chunks.\n"
        "2. read_file(path: str, start_line: int | null = null, end_line: int | null = null)\n"
        "   Use this to inspect a repository file or a focused line range.\n"
        "3. list_files(pattern: str | null = null)\n"
        "   Use this to list indexed files and narrow the search space.\n\n"
        "Response rules:\n"
        "- Always include exactly one <thought>...</thought> block.\n"
        "- If you need a tool, include exactly one <tool_call>...</tool_call> block.\n"
        "- The <tool_call> block must contain a single JSON object with keys `name` and `arguments`.\n"
        "- If you already have enough information, return <final_answer>...</final_answer> instead.\n"
        "- Do not invent tool outputs.\n"
        "- If the answer is obvious and needs no tool, respond directly with <final_answer>.\n"
        f"- You have at most {max_steps} tool steps before you must stop.\n\n"
        "Examples:\n"
        "<thought>I should search for the entry point first.</thought>\n"
        f"<tool_call>{example_search}</tool_call>\n\n"
        "<thought>The retrieved chunk points to python/main.py, so I should inspect the full function.</thought>\n"
        f"<tool_call>{example_read}</tool_call>\n\n"
        "<thought>The user only asked which Python files exist, so listing them is enough.</thought>\n"
        f"<tool_call>{example_list}</tool_call>\n\n"
        "<thought>The question is a simple capability question, so I can answer directly.</thought>\n"
        "<final_answer>I can search indexed code, read repository files, and list files inside the repo.</final_answer>\n\n"
        f"User Question:\n{query}\n\n"
        f"Scratchpad:\n{format_react_history(history_blocks)}\n"
    )


def build_react_best_effort_prompt(query: str, history_blocks: list[str]) -> str:
    return (
        "You are finishing a ReAct-style code investigation after the tool-step budget has been used.\n"
        "No more tool calls are allowed.\n"
        "Write the best grounded final answer you can using only the existing scratchpad observations.\n"
        "Requirements:\n"
        "- summarize the strongest grounded findings first\n"
        "- mention file paths when they appear in the observations\n"
        "- explicitly say when the evidence is incomplete\n"
        "- do not invent new tool results or files\n\n"
        f"User Question:\n{query}\n\n"
        f"Scratchpad:\n{format_react_history(history_blocks)}\n"
    )
