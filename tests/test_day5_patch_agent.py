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
        repo_root / "src" / "auth_service.py",
        '"""Authentication service for the demo repository."""\n\n'
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    token_ttl = config["token_ttl"]\n'
        '    audit_mode = config.get("audit_mode", "off")\n'
        '    return f"{username}:{token_ttl}:{audit_mode}"\n\n'
        "def build_login_payload(username: str, password: str) -> dict[str, str]:\n"
        '    return {"username": username, "password": password}\n',
    )
    _write_text(
        repo_root / "src" / "app.py",
        "from auth_service import login_user\n\n"
        "def main() -> str:\n"
        '    return login_user("demo", "secret", {"token_ttl": "3600"})\n',
    )
    _write_text(
        repo_root / "src" / "config.py",
        "def load_runtime_config() -> dict[str, str]:\n"
        '    return {"token_ttl": "3600", "audit_mode": "off"}\n',
    )
    _write_text(
        repo_root / "docs" / "login_patch_notes.md",
        "# Login Patch Notes\n\n"
        "This markdown file talks about improving login validation and logging.\n"
        "Use the Python source as the ground truth.\n",
    )


def _overlap_ratio(left_start: int, left_end: int, right_start: int, right_end: int) -> float:
    overlap_start = max(left_start, right_start)
    overlap_end = min(left_end, right_end)
    if overlap_start > overlap_end:
        return 0.0
    overlap = overlap_end - overlap_start + 1
    shorter = min(left_end - left_start + 1, right_end - right_start + 1)
    return overlap / shorter


def run_day5_patch_agent_local_test() -> tuple[str, str, list[str]]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=6,
            chunk_overlap=4,
            embedding_dimension=128,
        )
        agent = CodebaseQAAgent.from_metadata(metadata_path)

        query = "How should I add input validation and error handling to the login flow?"
        sources = agent.retrieve(query, top_k=4, intent="patch")
        assert len(sources) == 4
        assert sources[0].chunk.relative_path == "src/auth_service.py"
        assert sources[0].chunk.language == "python"
        assert sources[0].chunk.relative_path != "docs/login_patch_notes.md"

        for index, left in enumerate(sources):
            for right in sources[index + 1 :]:
                if left.chunk.relative_path != right.chunk.relative_path:
                    continue
                overlap = _overlap_ratio(
                    left.chunk.start_line,
                    left.chunk.end_line,
                    right.chunk.start_line,
                    right.chunk.end_line,
                )
                assert overlap < 0.8

        result = agent.patch(query, top_k=4, answer_mode="local")
        assert result.backend == "local"
        assert result.notice is None
        assert result.sources[0].chunk.relative_path == "src/auth_service.py"
        assert "Suggested file: src/auth_service.py" in result.suggestion
        assert "Suggested change area: def login_user" in result.suggestion
        assert "Reason:" in result.suggestion
        assert "Patch sketch:" in result.suggestion
        assert "```diff" in result.suggestion
        assert "ValueError" in result.suggestion
        assert "token_ttl" in result.suggestion
        assert query in result.prompt

        paths = [f"{source.chunk.relative_path}:{source.chunk.start_line}-{source.chunk.end_line}" for source in result.sources]
        return result.backend, result.sources[0].chunk.relative_path, paths


def run_day5_patch_agent_llm_test() -> tuple[str, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=6,
            chunk_overlap=4,
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
            captured["body"] = json.loads(api_request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Patch suggestion: update src/auth_service.py around login_user to add validation before config access."
                            }
                        }
                    ]
                }
            )

        agent = CodebaseQAAgent.from_metadata(metadata_path, llm_settings=settings)
        with patch("codebase_copilot.llm.request.urlopen", side_effect=_fake_urlopen):
            result = agent.patch(
                "How should I add input validation and error handling to the login flow?",
                top_k=4,
                answer_mode="llm",
            )

        assert result.backend == "llm"
        assert result.notice is None
        assert "src/auth_service.py" in result.suggestion
        body = captured["body"]
        assert captured["url"] == "https://example.com/v1/chat/completions"
        assert captured["timeout"] == 5.0
        assert body["model"] == "qwen3.5-122b-a10b"
        assert "Patch Request:" in body["messages"][0]["content"]
        assert "Code Context:" in body["messages"][0]["content"]
        assert "src/auth_service.py" in body["messages"][0]["content"]

        return result.backend, str(captured["url"])


def run_day5_patch_agent_fallback_test() -> tuple[str, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=6,
            chunk_overlap=4,
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
            result = agent.patch(
                "How should I add input validation and error handling to the login flow?",
                top_k=4,
                answer_mode="auto",
            )

        assert result.backend == "local"
        assert result.notice is not None
        assert "fell back to the local patch suggester" in result.notice
        assert "Suggested file: src/auth_service.py" in result.suggestion

        try:
            with patch("codebase_copilot.llm.request.urlopen", side_effect=URLError("offline")):
                agent.patch(
                    "How should I add input validation and error handling to the login flow?",
                    top_k=4,
                    answer_mode="llm",
                )
        except LLMRequestError as exc:
            return result.backend, str(exc)

        raise AssertionError("expected strict llm patch mode to raise on request failure")


def test_day5_patch_agent() -> None:
    run_day5_patch_agent_local_test()
    run_day5_patch_agent_llm_test()
    run_day5_patch_agent_fallback_test()


def main() -> int:
    backend, primary_path, paths = run_day5_patch_agent_local_test()
    llm_backend, llm_url = run_day5_patch_agent_llm_test()
    fallback_backend, fallback_error = run_day5_patch_agent_fallback_test()
    print("Day 5 patch agent test passed.")
    print(f"backend={backend}")
    print(f"primary_path={primary_path}")
    print(f"paths={paths}")
    print(f"llm_backend={llm_backend}")
    print(f"llm_url={llm_url}")
    print(f"fallback_backend={fallback_backend}")
    print(f"fallback_error={fallback_error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
