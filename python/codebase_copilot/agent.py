from __future__ import annotations

import json
import re
from pathlib import Path

from .embedder import HashingEmbedder
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
    """Deterministic fallback answerer used until a real LLM backend is wired in."""

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
        terms: list[str] = []
        for term in QUERY_TERM_PATTERN.findall(query.lower()):
            if term in STOP_WORDS:
                continue
            if len(term) == 1 and term.isascii():
                continue
            terms.append(term)
        return terms

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
    ) -> None:
        if loaded_index.embedding_provider != "hashing":
            raise ValueError(
                f"Unsupported embedding provider: {loaded_index.embedding_provider}. "
                "Only the local hashing embedder is supported right now."
            )

        self.loaded_index = loaded_index
        self.embedder = HashingEmbedder(dimension=loaded_index.embedding_dimension)
        self.answer_synthesizer = answer_synthesizer or LocalAnswerSynthesizer()
        self.retriever = VectorRetriever()
        self._chunk_by_id = {chunk.chunk_id: chunk for chunk in loaded_index.chunks}

        if loaded_index.chunks:
            # Day 3 persists chunk metadata only, so Day 4 rebuilds the in-memory index on load.
            embeddings = self.embedder.embed_texts(
                [chunk.to_embedding_text() for chunk in loaded_index.chunks]
            )
            self.retriever.add_items([chunk.chunk_id for chunk in loaded_index.chunks], embeddings)

    @classmethod
    def from_metadata(cls, metadata_path: str | Path) -> "CodebaseQAAgent":
        return cls(load_index_metadata(metadata_path))

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        if not query.strip():
            return []

        results = self.retriever.search(self.embedder.embed_text(query), top_k=top_k)
        return [
            RetrievedChunk(chunk=self._chunk_by_id[item_id], score=score)
            for item_id, score in results
            if item_id in self._chunk_by_id
        ]

    def ask(self, query: str, top_k: int = 4) -> AnswerResult:
        sources = self.retrieve(query, top_k=top_k)
        prompt = build_qa_prompt(query, sources)
        answer = self.answer_synthesizer.generate(query, sources)
        return AnswerResult(
            query=query,
            answer=answer,
            prompt=prompt,
            sources=sources,
        )