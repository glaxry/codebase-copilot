from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.llm import LLMSettings
from codebase_copilot.pipeline import build_index


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self._content = content

    def read(self) -> bytes:
        payload = {"choices": [{"message": {"content": self._content}}]}
        return json.dumps(payload).encode("utf-8")

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
        "from auth_service import login_user\n\n"
        "def main() -> str:\n"
        '    return login_user("demo", "secret", {"token_ttl": "3600"})\n'
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
    )
    _write_text(
        repo_root / "src" / "auth_service.py",
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    return f"{username}:{config[\'token_ttl\']}"\n',
    )


def run_day8_react_loop_test() -> tuple[int, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=12,
            chunk_overlap=3,
            embedding_dimension=128,
        )

        settings = LLMSettings(
            api_key="test-key",
            base_url="https://example.com/v1",
            model="qwen3.5-122b-a10b",
            timeout_seconds=5.0,
        )
        agent = CodebaseQAAgent.from_metadata(metadata_path, llm_settings=settings)

        scripted_responses = [
            _FakeResponse(
                "<thought>I should search for the entry point first.</thought>\n"
                '<tool_call>{"name":"search_codebase","arguments":{"query":"application entry point main function","top_k":3}}</tool_call>'
            ),
            _FakeResponse(
                "<thought>The search result is specific enough.</thought>\n"
                "<final_answer>The application entry point is src/app.py, which defines main() and the __main__ guard.</final_answer>"
            ),
        ]

        with patch("codebase_copilot.llm.request.urlopen", side_effect=scripted_responses):
            result = agent.agent_run("Where is the application entry point?", answer_mode="llm", max_steps=4)

        assert result.backend == "llm"
        assert len(result.steps) >= 1
        assert result.steps[0].tool_name == "search_codebase"
        assert "src/app.py" in result.steps[0].observation
        assert "src/app.py" in result.answer
        assert agent.execute_tool("missing_tool", {}) == "error=unknown tool: missing_tool"

        return len(result.steps), result.steps[0].tool_name or ""


def test_day8_react_loop() -> None:
    run_day8_react_loop_test()


def main() -> int:
    step_count, first_tool = run_day8_react_loop_test()
    print("Day 8 react loop test passed.")
    print(f"step_count={step_count}")
    print(f"first_tool={first_tool}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
