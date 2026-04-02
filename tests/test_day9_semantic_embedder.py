from __future__ import annotations

import json
import math
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.embedder import create_embedder
from codebase_copilot.pipeline import build_index


class _FakeSentenceTransformer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def get_sentence_embedding_dimension(self) -> int:
        return 6

    def encode(
        self,
        items: list[str],
        *,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> np.ndarray:
        assert convert_to_numpy is True
        assert normalize_embeddings is True
        assert show_progress_bar is False

        rows: list[np.ndarray] = []
        for text in items:
            lowered = text.lower()
            vector = np.array(
                [
                    float(any(token in lowered for token in ("login", "authenticate", "sign in"))),
                    float(any(token in lowered for token in ("password", "credential", "token"))),
                    float(any(token in lowered for token in ("config", "setting", "environment"))),
                    float(any(token in lowered for token in ("entry", "main", "__main__"))),
                    float(any(token in lowered for token in ("benchmark", "speed", "performance"))),
                    1.0,
                ],
                dtype=np.float32,
            )
            norm = float(np.linalg.norm(vector))
            rows.append(vector if norm == 0.0 else vector / norm)
        return np.vstack(rows).astype(np.float32)


def _install_fake_sentence_transformers() -> None:
    fake_module = types.ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = _FakeSentenceTransformer
    sys.modules["sentence_transformers"] = fake_module


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_demo_repo(repo_root: Path) -> None:
    _write_text(
        repo_root / "src" / "auth_service.py",
        '"""Authenticate users and issue session tokens."""\n\n'
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    return f"{username}:{config[\'token_ttl\']}"\n',
    )
    _write_text(
        repo_root / "src" / "config.py",
        '"""Load runtime settings for the application."""\n\n'
        "def load_runtime_config() -> dict[str, str]:\n"
        '    return {"token_ttl": "3600"}\n',
    )


def run_day9_semantic_embedder_test() -> tuple[str, int]:
    _install_fake_sentence_transformers()

    embedder = create_embedder("semantic", model_name="all-MiniLM-L6-v2")
    vector = embedder.embed_text("authenticate a user with credentials")
    matrix = embedder.embed_texts(["authenticate user", "load config"])

    assert vector.shape == (6,)
    assert matrix.shape == (2, 6)
    assert math.isclose(float(np.linalg.norm(vector)), 1.0, rel_tol=1e-4)

    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        result = build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=12,
            chunk_overlap=3,
            embedding_dimension=256,
            embedding_provider="semantic",
            embedding_model="all-MiniLM-L6-v2",
        )

        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert payload["embedding"]["provider"] == "semantic"
        assert payload["embedding"]["dimension"] == 6
        assert payload["embedding"]["model"] == "all-MiniLM-L6-v2"
        assert result.embedding_provider == "semantic"
        assert result.embedding_dimension == 6

        agent = CodebaseQAAgent.from_metadata(metadata_path)
        answer = agent.ask("How do we authenticate a user?", top_k=2, answer_mode="local")
        assert answer.backend == "local"
        assert "src/auth_service.py" in answer.answer

        return payload["embedding"]["provider"], result.embedding_dimension


def test_day9_semantic_embedder() -> None:
    run_day9_semantic_embedder_test()


def main() -> int:
    provider, dimension = run_day9_semantic_embedder_test()
    print("Day 9 semantic embedder test passed.")
    print(f"provider={provider}")
    print(f"dimension={dimension}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
