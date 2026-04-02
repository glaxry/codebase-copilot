from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from .agent import CodebaseQAAgent
from .config import DEFAULT_SEMANTIC_EMBEDDING_MODEL
from .pipeline import build_index


@dataclass(frozen=True)
class EmbeddingComparisonCase:
    query: str
    expected_path: str
    description: str


@dataclass(frozen=True)
class EmbeddingComparisonRow:
    query: str
    expected_path: str
    hashing_top1: str
    semantic_top1: str
    hashing_match: bool
    semantic_match: bool
    description: str


COMPARISON_CASES = [
    EmbeddingComparisonCase(
        query="How do we authenticate a user?",
        expected_path="src/auth/login.py",
        description="semantic synonym: authenticate -> login",
    ),
    EmbeddingComparisonCase(
        query="Where are runtime settings loaded?",
        expected_path="src/config/runtime.py",
        description="semantic synonym: settings -> config",
    ),
    EmbeddingComparisonCase(
        query="Which file performs similarity lookup over vectors?",
        expected_path="src/search/vector_search.py",
        description="semantic synonym: lookup -> search",
    ),
    EmbeddingComparisonCase(
        query="Where is the application entrypoint?",
        expected_path="src/cli/entry.py",
        description="semantic synonym: entrypoint -> command entry",
    ),
    EmbeddingComparisonCase(
        query="How are access rights checked?",
        expected_path="src/security/permission.py",
        description="semantic synonym: access rights -> permission",
    ),
]


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_embedding_comparison_repo(repo_root: Path) -> None:
    _write_text(
        repo_root / "src" / "auth" / "login.py",
        '"""Handle user login and issue a session token after credential checks."""\n\n'
        "def login_user(username: str, password: str) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    return f"{username}:token"\n',
    )
    _write_text(
        repo_root / "src" / "config" / "runtime.py",
        '"""Load runtime configuration and environment settings for the application."""\n\n'
        "def load_runtime_config() -> dict[str, str]:\n"
        '    return {"environment": "dev", "token_ttl": "3600"}\n',
    )
    _write_text(
        repo_root / "src" / "search" / "vector_search.py",
        '"""Perform vector search and cosine similarity lookup for ranked retrieval."""\n\n'
        "def search_vectors(query_vector: list[float]) -> list[int]:\n"
        "    return [0]\n",
    )
    _write_text(
        repo_root / "src" / "cli" / "entry.py",
        '"""Application command entry that wires the main CLI boot path."""\n\n'
        "def main() -> int:\n"
        "    return 0\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
    )
    _write_text(
        repo_root / "src" / "security" / "permission.py",
        '"""Check permissions and verify access rights for protected actions."""\n\n'
        "def has_permission(user_role: str, action: str) -> bool:\n"
        '    return user_role == "admin"\n',
    )


def _top1_path(agent: CodebaseQAAgent, query: str) -> str:
    results = agent.retrieve(query, top_k=1, intent="qa")
    if not results:
        return "<none>"
    return results[0].chunk.relative_path


def run_embedding_comparison(
    *,
    semantic_model: str = DEFAULT_SEMANTIC_EMBEDDING_MODEL,
) -> list[EmbeddingComparisonRow]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "comparison_repo"
        hashing_metadata = repo_root / "data" / "hashing_metadata.json"
        semantic_metadata = repo_root / "data" / "semantic_metadata.json"
        create_embedding_comparison_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=hashing_metadata,
            chunk_size=16,
            chunk_overlap=4,
            embedding_dimension=128,
            embedding_provider="hashing",
        )
        build_index(
            repo_root=repo_root,
            metadata_output=semantic_metadata,
            chunk_size=16,
            chunk_overlap=4,
            embedding_dimension=128,
            embedding_provider="semantic",
            embedding_model=semantic_model,
        )

        hashing_agent = CodebaseQAAgent.from_metadata(hashing_metadata)
        semantic_agent = CodebaseQAAgent.from_metadata(semantic_metadata)

        rows: list[EmbeddingComparisonRow] = []
        for case in COMPARISON_CASES:
            hashing_top1 = _top1_path(hashing_agent, case.query)
            semantic_top1 = _top1_path(semantic_agent, case.query)
            rows.append(
                EmbeddingComparisonRow(
                    query=case.query,
                    expected_path=case.expected_path,
                    hashing_top1=hashing_top1,
                    semantic_top1=semantic_top1,
                    hashing_match=hashing_top1 == case.expected_path,
                    semantic_match=semantic_top1 == case.expected_path,
                    description=case.description,
                )
            )
        return rows


def format_embedding_comparison_markdown(
    rows: list[EmbeddingComparisonRow],
    *,
    semantic_model: str = DEFAULT_SEMANTIC_EMBEDDING_MODEL,
) -> str:
    hashing_hits = sum(1 for row in rows if row.hashing_match)
    semantic_hits = sum(1 for row in rows if row.semantic_match)
    table_lines = [
        "| Query | Expected Top-1 | Hashing Top-1 | Semantic Top-1 | Hashing Match | Semantic Match | Note |",
        "| --- | --- | --- | --- | :---: | :---: | --- |",
    ]
    for row in rows:
        table_lines.append(
            f"| {row.query} | {row.expected_path} | {row.hashing_top1} | {row.semantic_top1} | "
            f"{'yes' if row.hashing_match else 'no'} | {'yes' if row.semantic_match else 'no'} | {row.description} |"
        )

    return "\n".join(
        [
            "# Embedding Comparison",
            "",
            "This report compares the existing hashing embedder with the new semantic embedder on a small synthetic codebase that was designed to surface semantic synonym gaps.",
            "",
            f"- semantic model: `{semantic_model}`",
            f"- query count: {len(rows)}",
            f"- hashing top-1 hits: {hashing_hits}/{len(rows)}",
            f"- semantic top-1 hits: {semantic_hits}/{len(rows)}",
            "",
            "## Results",
            "",
            *table_lines,
            "",
            "## Takeaways",
            "",
            "- hashing is lightweight and deterministic, but it relies heavily on exact token overlap",
            "- semantic embeddings handle synonym-style queries much better when the wording differs from the code tokens",
            "- the native C++ retriever remains reusable because it only depends on vectors, not on how they were produced",
        ]
    )


def write_embedding_comparison_report(
    output_path: str | Path,
    *,
    semantic_model: str = DEFAULT_SEMANTIC_EMBEDDING_MODEL,
) -> Path:
    rows = run_embedding_comparison(semantic_model=semantic_model)
    report = format_embedding_comparison_markdown(rows, semantic_model=semantic_model)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return path
