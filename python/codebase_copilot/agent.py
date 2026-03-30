from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

from .embedder import HashingEmbedder
from .llm import LLMRequestError, LLMSettings, OpenAICompatibleChatSynthesizer
from .models import AnswerResult, CodeChunk, LoadedIndex, RetrievedChunk
from .prompt import build_qa_prompt
from .retriever import VectorRetriever


QUERY_TERM_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[\u4e00-\u9fff]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "does",
    "file",
    "for",
    "how",
    "is",
    "of",
    "the",
    "what",
    "where",
    "which",
}
SOURCE_DIRECTORIES = {"src", "python", "cpp", "include"}
TEST_DIRECTORIES = {"test", "tests"}
DOC_DIRECTORIES = {"doc", "docs"}
CODE_LINE_PREFIXES = (
    "def ",
    "class ",
    "from ",
    "import ",
    "return ",
    "if ",
    "for ",
    "while ",
    "#include",
    "struct ",
    "void ",
    "int ",
)


def _extract_query_terms(text: str) -> list[str]:
    terms: list[str] = []
    for term in QUERY_TERM_PATTERN.findall(text.lower()):
        if term in STOP_WORDS:
            continue
        if len(term) == 1 and term.isascii():
            continue
        terms.append(term)
    return terms


def _path_terms(relative_path: str) -> set[str]:
    return set(QUERY_TERM_PATTERN.findall(relative_path.lower()))


def _is_test_path(path: PurePosixPath) -> bool:
    return any(part.lower() in TEST_DIRECTORIES for part in path.parts) or path.name.startswith("test_")


def _is_doc_path(path: PurePosixPath) -> bool:
    return any(part.lower() in DOC_DIRECTORIES for part in path.parts) or path.suffix.lower() == ".md"


def _is_source_path(path: PurePosixPath) -> bool:
    if _is_doc_path(path) or _is_test_path(path):
        return False
    return any(part.lower() in SOURCE_DIRECTORIES for part in path.parts) or path.suffix.lower() != ".md"


def load_index_metadata(metadata_path: str | Path) -> LoadedIndex:
    path = Path(metadata_path).resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))

    embedding_config = payload["embedding"]
    chunking_config = payload["chunking"]
    chunks = [CodeChunk.from_record(record) for record in payload["chunks"]]

    return LoadedIndex(
        repo_root=str(payload["repo_root"]),
        metadata_path=path,
        embedding_provider=str(embedding_config["provider"]),
        embedding_dimension=int(embedding_config["dimension"]),
        chunk_size=int(chunking_config["chunk_size"]),
        chunk_overlap=int(chunking_config["chunk_overlap"]),
        file_count=int(payload["file_count"]),
        chunk_count=int(payload["chunk_count"]),
        chunks=chunks,
    )


class LocalAnswerSynthesizer:
    """Deterministic fallback answerer used when no LLM backend is configured."""

    def generate(self, query: str, sources: list[RetrievedChunk]) -> str:
        if not sources:
            return "No relevant indexed chunks were found for the question."

        primary = sources[0].chunk
        evidence_lines = self._collect_evidence_lines(query, sources)
        response_lines = [
            f"The strongest match is {primary.relative_path} lines {primary.start_line}-{primary.end_line}.",
        ]

        if evidence_lines:
            response_lines.append("Relevant lines:")
            response_lines.extend(f"- {line}" for line in evidence_lines)

        if len(sources) > 1:
            related_sources = ", ".join(
                f"{source.chunk.relative_path}:{source.chunk.start_line}-{source.chunk.end_line}"
                for source in sources[1:]
            )
            response_lines.append(f"Additional sources: {related_sources}")

        return "\n".join(response_lines)

    @staticmethod
    def _query_terms(query: str) -> list[str]:
        return _extract_query_terms(query)

    def _collect_evidence_lines(self, query: str, sources: list[RetrievedChunk]) -> list[str]:
        selected = self._select_lines_from_chunk(query, sources[0], limit=3, include_fallback=True)
        seen = set(selected)

        if len(selected) >= 4:
            return selected[:4]

        for source in sources[1:]:
            for line in self._select_lines_from_chunk(query, source, limit=1, include_fallback=False):
                if line in seen:
                    continue
                seen.add(line)
                selected.append(line)
                if len(selected) == 4:
                    return selected

        return selected

    def _select_lines_from_chunk(
        self,
        query: str,
        source: RetrievedChunk,
        limit: int,
        include_fallback: bool,
    ) -> list[str]:
        query_terms = self._query_terms(query)
        candidates: list[tuple[float, str]] = []

        for line in source.chunk.text.splitlines():
            normalized = line.strip()
            if not normalized:
                continue

            # Prefer lines that echo the query terms so the offline answer stays grounded.
            score = self._score_line(normalized, query_terms)
            if score <= 0.0:
                continue
            candidates.append((score + source.score, normalized))

        candidates.sort(key=lambda item: item[0], reverse=True)

        selected: list[str] = []
        seen: set[str] = set()
        for _, line in candidates:
            if line in seen:
                continue
            seen.add(line)
            selected.append(line)
            if len(selected) == limit:
                return selected

        if not include_fallback:
            return selected

        for line in source.chunk.text.splitlines():
            normalized = line.strip()
            if not normalized or normalized in seen:
                continue
            if normalized.startswith(("def ", "class ", "struct ", "int ", "void ", "return ")):
                seen.add(normalized)
                selected.append(normalized)
                if len(selected) == limit:
                    return selected

        for line in source.chunk.text.splitlines():
            normalized = line.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            selected.append(normalized)
            if len(selected) == limit:
                return selected

        return selected

    @staticmethod
    def _score_line(line: str, query_terms: list[str]) -> float:
        line_lower = line.lower()
        overlap_score = float(sum(1 for term in query_terms if term in line_lower))
        if overlap_score == 0.0 and query_terms:
            return 0.0

        structure_bonus = 0.0
        if line.startswith(("def ", "class ", "struct ", "int ", "void ", "return ")):
            structure_bonus += 0.25
        if '"""' in line or "'''" in line or line.startswith("#"):
            structure_bonus += 0.15
        return overlap_score + structure_bonus


class CodebaseQAAgent:
    """Load Day 3 metadata, rebuild the retriever in memory, and answer repo questions."""

    def __init__(
        self,
        loaded_index: LoadedIndex,
        answer_synthesizer: LocalAnswerSynthesizer | None = None,
        llm_settings: LLMSettings | None = None,
    ) -> None:
        if loaded_index.embedding_provider != "hashing":
            raise ValueError(
                f"Unsupported embedding provider: {loaded_index.embedding_provider}. "
                "Only the local hashing embedder is supported right now."
            )

        self.loaded_index = loaded_index
        self.embedder = HashingEmbedder(dimension=loaded_index.embedding_dimension)
        self.answer_synthesizer = answer_synthesizer or LocalAnswerSynthesizer()
        self.llm_synthesizer = (
            OpenAICompatibleChatSynthesizer(llm_settings) if llm_settings is not None else None
        )
        self.retriever = VectorRetriever()
        self._chunk_by_id = {chunk.chunk_id: chunk for chunk in loaded_index.chunks}

        if loaded_index.chunks:
            # Day 3 persists chunk metadata only, so Day 4 rebuilds the native retriever in memory on load.
            embeddings = self.embedder.embed_texts(
                [chunk.to_embedding_text() for chunk in loaded_index.chunks]
            )
            self.retriever.add_items([chunk.chunk_id for chunk in loaded_index.chunks], embeddings)

    @classmethod
    def from_metadata(
        cls,
        metadata_path: str | Path,
        llm_settings: LLMSettings | None = None,
    ) -> "CodebaseQAAgent":
        return cls(load_index_metadata(metadata_path), llm_settings=llm_settings)

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        if not query.strip():
            return []

        candidate_count = min(self.retriever.size, max(top_k * 16, 128))
        query_terms = _extract_query_terms(query)
        results = self.retriever.search(self.embedder.embed_text(query), top_k=candidate_count)
        candidates = [
            RetrievedChunk(chunk=self._chunk_by_id[item_id], score=score)
            for item_id, score in results
            if item_id in self._chunk_by_id
        ]
        ranked_candidates = sorted(
            candidates,
            key=lambda candidate: self._rerank_score(query_terms, candidate),
            reverse=True,
        )

        wants_docs = any(term in {"doc", "docs", "readme", "markdown", "note", "notes"} for term in query_terms)
        wants_tests = any(term in {"test", "tests", "testing"} or term.startswith("test_") for term in query_terms)
        selected: list[RetrievedChunk] = []
        deferred: list[RetrievedChunk] = []

        for candidate in ranked_candidates:
            candidate_path = PurePosixPath(candidate.chunk.relative_path)
            if not wants_docs and _is_doc_path(candidate_path):
                deferred.append(candidate)
                continue
            if not wants_tests and _is_test_path(candidate_path):
                deferred.append(candidate)
                continue
            selected.append(candidate)
            if len(selected) == top_k:
                return selected

        for candidate in deferred:
            selected.append(candidate)
            if len(selected) == top_k:
                break

        return selected

    def _rerank_score(self, query_terms: list[str], candidate: RetrievedChunk) -> float:
        chunk = candidate.chunk
        path = PurePosixPath(chunk.relative_path)
        score = candidate.score

        wants_docs = any(term in {"doc", "docs", "readme", "markdown", "note", "notes"} for term in query_terms)
        wants_tests = any(term in {"test", "tests", "testing"} or term.startswith("test_") for term in query_terms)
        wants_entrypoint = "entrypoint" in query_terms or ("entry" in query_terms and "point" in query_terms)
        wants_cli = any(term in {"cli", "command", "commands", "subcommand", "subcommands"} for term in query_terms)

        if _is_doc_path(path):
            score += 0.18 if wants_docs else -0.30
        elif _is_test_path(path):
            score += 0.15 if wants_tests else -0.08
        elif _is_source_path(path):
            score += 0.18

        path_overlap = len(_path_terms(chunk.relative_path).intersection(query_terms))
        score += min(path_overlap, 4) * 0.05

        chunk_text_lower = chunk.text.lower()
        if wants_entrypoint:
            if path.stem == "main":
                score += 0.35
            if "def main(" in chunk_text_lower:
                score += 0.40
            if '__main__' in chunk_text_lower:
                score += 0.55
            if "systemexit(main())" in chunk_text_lower.replace(" ", ""):
                score += 0.30

        if wants_cli:
            if "argparse" in chunk_text_lower:
                score += 0.20
            if "add_parser(" in chunk_text_lower:
                score += 0.25
            if path.stem == "main":
                score += 0.15

        code_line_hits = 0
        for line in chunk.text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(CODE_LINE_PREFIXES):
                code_line_hits += 1
            elif any(token in stripped for token in ("{", "}", "(", ")", "=", ";")):
                code_line_hits += 1

        if not wants_docs:
            score += min(code_line_hits, 6) * 0.02

        return score

    def ask(self, query: str, top_k: int = 4, answer_mode: str = "auto") -> AnswerResult:
        if answer_mode not in {"auto", "local", "llm"}:
            raise ValueError(f"Unsupported answer mode: {answer_mode}")

        sources = self.retrieve(query, top_k=top_k)
        prompt = build_qa_prompt(query, sources)

        if answer_mode == "local":
            answer = self.answer_synthesizer.generate(query, sources)
            return AnswerResult(
                query=query,
                answer=answer,
                prompt=prompt,
                sources=sources,
                backend="local",
            )

        if self.llm_synthesizer is None:
            if answer_mode == "llm":
                raise ValueError(
                    "LLM mode requested but no API key was configured. Set CODEBASE_COPILOT_LLM_API_KEY "
                    "or OPENAI_API_KEY."
                )
            answer = self.answer_synthesizer.generate(query, sources)
            return AnswerResult(
                query=query,
                answer=answer,
                prompt=prompt,
                sources=sources,
                backend="local",
            )

        try:
            answer = self.llm_synthesizer.generate(prompt)
            return AnswerResult(
                query=query,
                answer=answer,
                prompt=prompt,
                sources=sources,
                backend="llm",
            )
        except LLMRequestError as exc:
            if answer_mode == "llm":
                raise

            answer = self.answer_synthesizer.generate(query, sources)
            return AnswerResult(
                query=query,
                answer=answer,
                prompt=prompt,
                sources=sources,
                backend="local",
                notice=f"LLM request failed and the agent fell back to the local answerer: {exc}",
            )