from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.llm import LLMRequestError, LLMSettings
from codebase_copilot.pipeline import build_index


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_demo_repo(repo_root: Path) -> None:
    _write_text(
        repo_root / "src" / "app.py",
        '"""Application entry point for the demo repository."""\n\n'
        "from config import load_runtime_config\n"
        "from auth_service import login_user\n\n"
        "def main():\n"
        "    config = load_runtime_config()\n"
        '    return login_user("demo", "secret", config)\n',
    )
    _write_text(
        repo_root / "src" / "auth_service.py",
        '"""Authentication service that validates username and password before issuing a token."""\n\n'
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    token_ttl = config["token_ttl"]\n'
        '    return f"{username}:{token_ttl}"\n',
    )
    _write_text(
        repo_root / "src" / "config.py",
        '"""Configuration loader for token settings."""\n\n'
        "import os\n\n"
        "def load_runtime_config() -> dict[str, str]:\n"
        "    return {\n"
        '        "environment": os.getenv("APP_ENV", "dev"),\n'
        '        "token_ttl": os.getenv("TOKEN_TTL", "3600"),\n'
        "    }\n",
    )


def run_day4_llm_backend_test() -> tuple[str, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=20,
            chunk_overlap=5,
            embedding_dimension=128,
        )

        settings = LLMSettings(
            api_key="test-key",
            base_url="https://example.com/v1",
            model="qwen3.5-122b-a10b",
            timeout_seconds=5.0,
        )
        captured: dict[str, object] = {}

        def _fake_urlopen(api_request, timeout):
            captured["url"] = api_request.full_url
            captured["auth"] = api_request.get_header("Authorization")
            captured["body"] = json.loads(api_request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "LLM answer: the entry point is src/app.py and the main function loads config before login."
                            }
                        }
                    ]
                }
            )

        agent = CodebaseQAAgent.from_metadata(metadata_path, llm_settings=settings)
        with patch("codebase_copilot.llm.request.urlopen", side_effect=_fake_urlopen):
            result = agent.ask("Where is the application entry point?", top_k=3, answer_mode="llm")

        assert result.backend == "llm"
        assert result.notice is None
        assert "src/app.py" in result.answer
        assert captured["url"] == "https://example.com/v1/chat/completions"
        assert captured["auth"] == "Bearer test-key"
        assert captured["timeout"] == 5.0
        body = captured["body"]
        assert body["model"] == "qwen3.5-122b-a10b"
        assert body["messages"][0]["role"] == "user"
        assert "Where is the application entry point?" in body["messages"][0]["content"]
        assert "src/app.py" in body["messages"][0]["content"]

        return result.backend, str(captured["url"])


def run_day4_llm_fallback_test() -> tuple[str, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=20,
            chunk_overlap=5,
            embedding_dimension=128,
        )

        settings = LLMSettings(
            api_key="test-key",
            base_url="https://example.com/v1",
            model="qwen3.5-122b-a10b",
            timeout_seconds=5.0,
        )
        agent = CodebaseQAAgent.from_metadata(metadata_path, llm_settings=settings)

        with patch("codebase_copilot.llm.request.urlopen", side_effect=URLError("offline")):
            result = agent.ask("Where is the application entry point?", top_k=3, answer_mode="auto")

        assert result.backend == "local"
        assert result.notice is not None
        assert "fell back to the local answerer" in result.notice
        assert "src/app.py" in result.answer

        try:
            with patch("codebase_copilot.llm.request.urlopen", side_effect=URLError("offline")):
                agent.ask("Where is the application entry point?", top_k=3, answer_mode="llm")
        except LLMRequestError as exc:
            return result.backend, str(exc)

        raise AssertionError("expected strict llm mode to raise on request failure")


def test_day4_llm_backend() -> None:
    run_day4_llm_backend_test()
    run_day4_llm_fallback_test()


def main() -> int:
    backend, url = run_day4_llm_backend_test()
    fallback_backend, fallback_error = run_day4_llm_fallback_test()
    print("Day 4 llm backend test passed.")
    print(f"backend={backend}")
    print(f"url={url}")
    print(f"fallback_backend={fallback_backend}")
    print(f"fallback_error={fallback_error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())