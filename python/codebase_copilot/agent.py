from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

from .embedder import HashingEmbedder
from .llm import LLMRequestError, LLMSettings, OpenAICompatibleChatSynthesizer
from .models import AnswerResult, CodeChunk, LoadedIndex, PatchSuggestionResult, RetrievedChunk
from .prompt import build_patch_prompt, build_qa_prompt
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
VALIDATION_TERMS = {
    "param",
    "params",
    "parameter",
    "parameters",
    "validate",
    "validates",
    "validated",
    "validation",
    "input",
    "inputs",
    "check",
    "checks",
    "guard",
    "required",
    "empty",
    "username",
    "password",
}
LOGGING_TERMS = {
    "log",
    "logs",
    "logged",
    "logging",
    "logger",
    "trace",
    "debug",
    "info",
    "warning",
    "warn",
    "audit",
}
EXCEPTION_TERMS = {
    "exception",
    "exceptions",
    "error",
    "errors",
    "raise",
    "raises",
    "except",
    "try",
    "failure",
    "failures",
    "handle",
    "handling",
}
PATCH_REQUEST_TERMS = {
    "add",
    "change",
    "improve",
    "modify",
    "patch",
    "refactor",
    "suggest",
    "update",
}


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


def _query_has_any(query_terms: list[str], focus_terms: set[str]) -> bool:
    return any(term in focus_terms for term in query_terms)


def _normalized_chunk_lines(text: str) -> tuple[str, ...]:
    return tuple(line.strip().lower() for line in text.splitlines() if line.strip())


def _line_overlap_ratio(left: CodeChunk, right: CodeChunk) -> float:
    if left.relative_path != right.relative_path:
        return 0.0

    overlap_start = max(left.start_line, right.start_line)
    overlap_end = min(left.end_line, right.end_line)
    if overlap_start > overlap_end:
        return 0.0

    overlap = overlap_end - overlap_start + 1
    shorter = min(left.line_count, right.line_count)
    if shorter <= 0:
        return 0.0
    return overlap / shorter


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


class LocalPatchSynthesizer:
    """Deterministic patch suggester used when no LLM backend is configured."""

    def generate(self, query: str, sources: list[RetrievedChunk]) -> str:
        if not sources:
            return "No relevant indexed chunks were found for the patch request."

        primary = sources[0].chunk
        focus_terms = self._classify_focuses(query)
        target_line = self._find_target_line(primary)
        anchor_lines = self._select_anchor_lines(primary)
        patch_lines = self._build_patch_sketch(primary, target_line, focus_terms, anchor_lines)

        response_lines = [f"Suggested file: {primary.relative_path}"]
        if target_line:
            response_lines.append(f"Suggested change area: {target_line}")
        response_lines.append("Reason:")
        response_lines.extend(
            f"- {reason}"
            for reason in self._build_reason_lines(primary, focus_terms, target_line, anchor_lines, sources)
        )
        response_lines.append("Patch sketch:")
        response_lines.append("```diff")
        response_lines.extend(patch_lines)
        response_lines.append("```")

        related_sources = self._format_related_sources(sources[1:])
        if related_sources:
            response_lines.append(f"Related context: {related_sources}")

        return "\n".join(response_lines)

    @staticmethod
    def _query_terms(query: str) -> list[str]:
        return _extract_query_terms(query)

    def _classify_focuses(self, query: str) -> list[str]:
        query_terms = self._query_terms(query)
        focuses: list[str] = []
        if _query_has_any(query_terms, VALIDATION_TERMS):
            focuses.append("validation")
        if _query_has_any(query_terms, LOGGING_TERMS):
            focuses.append("logging")
        if _query_has_any(query_terms, EXCEPTION_TERMS):
            focuses.append("exception")
        if not focuses:
            focuses.append("generic")
        return focuses

    @staticmethod
    def _find_target_line(chunk: CodeChunk) -> str | None:
        for line in chunk.text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("def ", "class ", "struct ", "void ", "int ")):
                return stripped
        for line in chunk.text.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
        return None

    @staticmethod
    def _extract_parameter_names(target_line: str | None) -> list[str]:
        if target_line is None or not target_line.startswith("def "):
            return []

        match = re.search(r"\((.*)\)", target_line)
        if match is None:
            return []

        parameters: list[str] = []
        for part in match.group(1).split(","):
            name = part.strip()
            if not name:
                continue
            name = name.split(":", 1)[0].strip()
            name = name.split("=", 1)[0].strip()
            if name in {"self", "cls", "*", "**kwargs", "*args"}:
                continue
            if name.startswith("**"):
                name = name[2:]
            elif name.startswith("*"):
                name = name[1:]
            if name:
                parameters.append(name)
        return parameters

    @staticmethod
    def _extract_function_name(target_line: str | None) -> str | None:
        if target_line is None or not target_line.startswith("def "):
            return None
        match = re.match(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", target_line)
        return match.group(1) if match is not None else None

    def _build_reason_lines(
        self,
        primary: CodeChunk,
        focus_terms: list[str],
        target_line: str | None,
        anchor_lines: list[str],
        sources: list[RetrievedChunk],
    ) -> list[str]:
        reasons: list[str] = []
        if target_line:
            reasons.append(
                f"{primary.relative_path} is the highest-confidence edit target because the retrieved chunk already contains `{target_line}`."
            )
        else:
            reasons.append(
                f"{primary.relative_path} is the highest-confidence edit target because the top chunk covers lines {primary.start_line}-{primary.end_line}."
            )

        if "validation" in focus_terms:
            if any("raise ValueError" in line for line in anchor_lines):
                reasons.append(
                    "The current code already uses `ValueError` guards, so stronger input validation fits the existing failure style."
                )
            else:
                reasons.append(
                    "This path consumes request data directly, so validation should happen before the existing business logic runs."
                )

        if "logging" in focus_terms:
            reasons.append(
                "The retrieved chunk does not show any logging calls, so adding logs here would improve traceability at the actual execution point."
            )

        if "exception" in focus_terms:
            risky_line = next((line for line in anchor_lines if "[" in line or "get(" in line), None)
            if risky_line is not None:
                reasons.append(
                    f"The chunk performs direct data access via `{risky_line}`, so wrapping that path makes error handling more explicit."
                )
            else:
                reasons.append(
                    "The retrieved logic does not expose explicit exception translation, so this is a reasonable place to add it."
                )

        if "generic" in focus_terms:
            reasons.append(
                "The patch sketch stays close to the retrieved lines so the suggested change remains grounded in the indexed code."
            )

        related_sources = self._format_related_sources(sources[1:])
        if related_sources:
            reasons.append(f"Supporting context also points to {related_sources}.")

        return reasons[:4]

    @staticmethod
    def _select_anchor_lines(chunk: CodeChunk, limit: int = 4) -> list[str]:
        selected: list[str] = []
        seen: set[str] = set()
        for line in chunk.text.splitlines():
            stripped = line.strip()
            if not stripped or stripped in seen:
                continue
            if stripped.startswith(("def ", "class ", "if ", "try:", "except ", "return ", "raise ")):
                seen.add(stripped)
                selected.append(stripped)
            elif "=" in stripped or "[" in stripped or ".get(" in stripped:
                seen.add(stripped)
                selected.append(stripped)
            if len(selected) == limit:
                return selected

        for line in chunk.text.splitlines():
            stripped = line.strip()
            if not stripped or stripped in seen:
                continue
            seen.add(stripped)
            selected.append(stripped)
            if len(selected) == limit:
                return selected

        return selected

    def _build_patch_sketch(
        self,
        primary: CodeChunk,
        target_line: str | None,
        focus_terms: list[str],
        anchor_lines: list[str],
    ) -> list[str]:
        parameters = self._extract_parameter_names(target_line)
        function_name = self._extract_function_name(target_line)
        patch_lines = [f"@@ {primary.relative_path}:{primary.start_line}-{primary.end_line} @@"]

        if target_line:
            patch_lines.append(f" {target_line}")
        else:
            patch_lines.append(f" # Update {primary.relative_path} near lines {primary.start_line}-{primary.end_line}")

        additions: list[str] = []
        if "validation" in focus_terms:
            additions.extend(self._validation_additions(parameters))
        if "logging" in focus_terms:
            additions.extend(self._logging_additions(function_name or PurePosixPath(primary.relative_path).stem))
        if "exception" in focus_terms:
            additions.extend(self._exception_additions(anchor_lines))
        if not additions:
            additions.extend(self._generic_additions())

        seen_lines: set[str] = set()
        for line in additions:
            if line in seen_lines:
                continue
            seen_lines.add(line)
            patch_lines.append(line)

        for line in anchor_lines:
            if target_line and line == target_line:
                continue
            patch_lines.append(f" {line}")

        return patch_lines

    @staticmethod
    def _validation_additions(parameters: list[str]) -> list[str]:
        preferred_parameters = [param for param in parameters if param not in {"config", "kwargs", "args"}]
        target_parameters = preferred_parameters[:2]

        additions: list[str] = []
        for name in target_parameters:
            additions.append(f"+    {name} = {name}.strip() if isinstance({name}, str) else {name}")

        if target_parameters:
            guard_expression = " or ".join(f"not {name}" for name in target_parameters)
            message = " and ".join(target_parameters)
            additions.extend(
                [
                    f"+    if {guard_expression}:",
                    f'+        raise ValueError("{message} must be provided")',
                ]
            )
            if "password" in target_parameters:
                additions.extend(
                    [
                        "+    if len(password) < 8:",
                        '+        raise ValueError("password must be at least 8 characters")',
                    ]
                )
            return additions

        return [
            "+    # Validate the incoming arguments before continuing",
            "+    if invalid_input:",
            '+        raise ValueError("invalid request payload")',
        ]

    @staticmethod
    def _logging_additions(function_name: str) -> list[str]:
        return [
            f'+    logger.info("{function_name} started")',
            f'+    logger.warning("{function_name} rejected invalid input")',
        ]

    @staticmethod
    def _exception_additions(anchor_lines: list[str]) -> list[str]:
        config_line = next((line for line in anchor_lines if 'config["' in line or "config['" in line), None)
        if config_line is not None:
            return [
                "+    try:",
                f"+        {config_line}",
                "+    except KeyError as exc:",
                '+        raise ValueError("missing required configuration") from exc',
            ]

        return [
            "+    try:",
            "+        # existing logic",
            "+    except Exception as exc:",
            '+        raise ValueError("request handling failed") from exc',
        ]

    @staticmethod
    def _generic_additions() -> list[str]:
        return [
            "+    # Insert the requested behavior before the existing return path",
            "+    # Reuse the current validation and error-handling style where possible",
        ]

    @staticmethod
    def _format_related_sources(sources: list[RetrievedChunk]) -> str:
        rendered: list[str] = []
        seen: set[str] = set()
        for source in sources:
            chunk = source.chunk
            label = f"{chunk.relative_path}:{chunk.start_line}-{chunk.end_line}"
            if label in seen:
                continue
            seen.add(label)
            rendered.append(label)
            if len(rendered) == 3:
                break
        return ", ".join(rendered)


class CodebaseQAAgent:
    """Load Day 3 metadata, rebuild the retriever in memory, and answer repo questions."""

    def __init__(
        self,
        loaded_index: LoadedIndex,
        answer_synthesizer: LocalAnswerSynthesizer | None = None,
        patch_synthesizer: LocalPatchSynthesizer | None = None,
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
        self.patch_synthesizer = patch_synthesizer or LocalPatchSynthesizer()
        self.llm_synthesizer = (
            OpenAICompatibleChatSynthesizer(llm_settings) if llm_settings is not None else None
        )
        self.retriever = VectorRetriever()
        self._chunk_by_id = {chunk.chunk_id: chunk for chunk in loaded_index.chunks}

        if loaded_index.chunks:
            # Day 3 persists chunk metadata only, so later commands rebuild the native retriever in memory.
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

    def retrieve(self, query: str, top_k: int = 4, intent: str = "qa") -> list[RetrievedChunk]:
        if intent not in {"qa", "patch"}:
            raise ValueError(f"Unsupported retrieval intent: {intent}")
        if not query.strip() or top_k <= 0 or self.retriever.size == 0:
            return []

        candidate_count = min(self.retriever.size, max(top_k * 24, 128))
        query_terms = _extract_query_terms(query)
        results = self.retriever.search(self.embedder.embed_text(query), top_k=candidate_count)
        candidates = [
            RetrievedChunk(chunk=self._chunk_by_id[item_id], score=score)
            for item_id, score in results
            if item_id in self._chunk_by_id
        ]  # 二次排序
        ranked_candidates = sorted(
            candidates,
            key=lambda candidate: self._rerank_score(query_terms, candidate, intent),
            reverse=True,
        )
        return self._select_context_chunks(ranked_candidates, top_k, query_terms)

    def _select_context_chunks(
        self,
        ranked_candidates: list[RetrievedChunk],
        top_k: int,
        query_terms: list[str],
    ) -> list[RetrievedChunk]:
        wants_docs = _query_has_any(query_terms, {"doc", "docs", "readme", "markdown", "note", "notes"})
        wants_tests = any(term in {"test", "tests", "testing"} or term.startswith("test_") for term in query_terms)

        preferred: list[RetrievedChunk] = []
        deferred: list[RetrievedChunk] = []
        for candidate in ranked_candidates:
            candidate_path = PurePosixPath(candidate.chunk.relative_path)
            if not wants_docs and _is_doc_path(candidate_path):
                deferred.append(candidate)
                continue
            if not wants_tests and _is_test_path(candidate_path):
                deferred.append(candidate)
                continue
            preferred.append(candidate)

        selected: list[RetrievedChunk] = []
        path_counts: dict[str, int] = {}
        self._append_context_candidates(selected, path_counts, preferred, top_k, allow_path_overflow=False)
        if len(selected) < top_k:
            self._append_context_candidates(selected, path_counts, deferred, top_k, allow_path_overflow=False)
        if len(selected) < top_k:
            self._append_context_candidates(selected, path_counts, ranked_candidates, top_k, allow_path_overflow=True)
        return selected[:top_k]

    def _append_context_candidates(
        self,
        selected: list[RetrievedChunk],
        path_counts: dict[str, int],
        candidates: list[RetrievedChunk],
        top_k: int,
        *,
        allow_path_overflow: bool,
    ) -> None:
        for candidate in candidates:
            if any(existing.chunk.chunk_id == candidate.chunk.chunk_id for existing in selected):
                continue
            if self._is_near_duplicate(selected, candidate):
                continue

            path_key = candidate.chunk.relative_path
            if not allow_path_overflow and path_counts.get(path_key, 0) >= 2:
                continue

            selected.append(candidate)
            path_counts[path_key] = path_counts.get(path_key, 0) + 1
            if len(selected) == top_k:
                return

    @staticmethod
    def _is_near_duplicate(selected: list[RetrievedChunk], candidate: RetrievedChunk) -> bool:
        candidate_lines = _normalized_chunk_lines(candidate.chunk.text)
        for existing in selected:
            if existing.chunk.relative_path != candidate.chunk.relative_path:
                continue
            if _line_overlap_ratio(existing.chunk, candidate.chunk) >= 0.6:
                return True
            if candidate_lines == _normalized_chunk_lines(existing.chunk.text):
                return True
        return False

    def _rerank_score(self, query_terms: list[str], candidate: RetrievedChunk, intent: str) -> float:
        chunk = candidate.chunk
        path = PurePosixPath(chunk.relative_path)
        score = candidate.score

        wants_docs = _query_has_any(query_terms, {"doc", "docs", "readme", "markdown", "note", "notes"})
        wants_tests = any(term in {"test", "tests", "testing"} or term.startswith("test_") for term in query_terms)
        wants_entrypoint = "entrypoint" in query_terms or ("entry" in query_terms and "point" in query_terms)
        wants_cli = any(term in {"cli", "command", "commands", "subcommand", "subcommands"} for term in query_terms)
        wants_validation = _query_has_any(query_terms, VALIDATION_TERMS)
        wants_logging = _query_has_any(query_terms, LOGGING_TERMS)
        wants_exceptions = _query_has_any(query_terms, EXCEPTION_TERMS)
        wants_patch = intent == "patch" or _query_has_any(query_terms, PATCH_REQUEST_TERMS)

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

        if wants_patch:
            if any(line.strip().startswith(("def ", "class ", "struct ")) for line in chunk.text.splitlines()):
                score += 0.18
            if wants_validation and any(token in chunk_text_lower for token in ("raise", "valueerror", "required", "validate", "if ")):
                score += 0.22
            if wants_logging and any(token in chunk_text_lower for token in ("log", "logger", "warning", "info", "audit")):
                score += 0.22
            if wants_exceptions and any(token in chunk_text_lower for token in ("try", "except", "raise", "error")):
                score += 0.22

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

    @staticmethod
    def _ensure_answer_mode(answer_mode: str) -> None:
        if answer_mode not in {"auto", "local", "llm"}:
            raise ValueError(f"Unsupported answer mode: {answer_mode}")

    def ask(self, query: str, top_k: int = 4, answer_mode: str = "auto") -> AnswerResult:
        self._ensure_answer_mode(answer_mode)

        sources = self.retrieve(query, top_k=top_k, intent="qa")
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

    def patch(self, query: str, top_k: int = 4, answer_mode: str = "auto") -> PatchSuggestionResult:
        self._ensure_answer_mode(answer_mode)

        sources = self.retrieve(query, top_k=top_k, intent="patch")
        prompt = build_patch_prompt(query, sources)

        if answer_mode == "local":
            suggestion = self.patch_synthesizer.generate(query, sources)
            return PatchSuggestionResult(
                query=query,
                suggestion=suggestion,
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
            suggestion = self.patch_synthesizer.generate(query, sources)
            return PatchSuggestionResult(
                query=query,
                suggestion=suggestion,
                prompt=prompt,
                sources=sources,
                backend="local",
            )

        try:
            suggestion = self.llm_synthesizer.generate(prompt)
            return PatchSuggestionResult(
                query=query,
                suggestion=suggestion,
                prompt=prompt,
                sources=sources,
                backend="llm",
            )
        except LLMRequestError as exc:
            if answer_mode == "llm":
                raise

            suggestion = self.patch_synthesizer.generate(query, sources)
            return PatchSuggestionResult(
                query=query,
                suggestion=suggestion,
                prompt=prompt,
                sources=sources,
                backend="local",
                notice=f"LLM request failed and the agent fell back to the local patch suggester: {exc}",
            )
