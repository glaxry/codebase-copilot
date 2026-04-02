from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.llm import LLMSettings
from codebase_copilot.pipeline import build_index
from codebase_copilot.tools import read_file


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


def _create_large_repo(repo_root: Path) -> None:
    large_file_lines = [f"line_{line_number:03d}" for line_number in range(1, 151)]
    _write_text(repo_root / "src" / "large.py", "\n".join(large_file_lines) + "\n")
    _write_text(
        repo_root / "src" / "app.py",
        '"""Application entry point for the demo repository."""\n\n'
        "def main() -> str:\n"
        '    return "ok"\n'
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
    )


def run_day8_read_file_window_test() -> tuple[str, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_large_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=24,
            chunk_overlap=4,
            embedding_dimension=128,
        )
        agent = CodebaseQAAgent.from_metadata(metadata_path)

        tool_output = agent.execute_tool(
            "read_file",
            {"path": "src/large.py", "start_line": 1, "end_line": 150},
        )
        assert "line_080" in tool_output
        assert "line_081" not in tool_output
        assert "more lines omitted" in tool_output

        direct_output = read_file(repo_root, "src/large.py", start_line=1, end_line=150)
        assert "line_100" in direct_output
        assert "line_101" not in direct_output

        return "line_080", "line_100"


def run_day8_best_effort_summary_test() -> tuple[int, str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_large_repo(repo_root)

        build_index(
            repo_root=repo_root,
            metadata_output=metadata_path,
            chunk_size=24,
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

        prompts: list[str] = []
        scripted_responses = [
            _FakeResponse(
                "<thought>I should search for the entry point first.</thought>\n"
                '<tool_call>{"name":"search_codebase","arguments":{"query":"application entry point main function","top_k":3}}</tool_call>'
            ),
            _FakeResponse(
                "<thought>I should inspect the most relevant file before answering.</thought>\n"
                '<tool_call>{"name":"read_file","arguments":{"path":"src/app.py","start_line":1,"end_line":40}}</tool_call>'
            ),
            _FakeResponse(
                "Best-effort summary: the strongest grounded evidence points to src/app.py, which defines main() and the __main__ guard."
            ),
        ]

        def _fake_urlopen(api_request, timeout):
            body = json.loads(api_request.data.decode("utf-8"))
            prompts.append(body["messages"][0]["content"])
            return scripted_responses[len(prompts) - 1]

        with patch("codebase_copilot.llm.request.urlopen", side_effect=_fake_urlopen):
            result = agent.agent_run("Where is the application entry point?", answer_mode="llm", max_steps=2)

        assert result.backend == "llm"
        assert len(prompts) == 3
        assert "No more tool calls are allowed" in prompts[2]
        assert "Observation" in prompts[2]
        assert "src/app.py" in prompts[2]
        assert "Best-effort summary:" in result.answer
        assert "reached the maximum number of steps" not in result.answer

        return len(prompts), result.answer


def test_day8_agent_tuning() -> None:
    run_day8_read_file_window_test()
    run_day8_best_effort_summary_test()


def main() -> int:
    observation_marker, direct_marker = run_day8_read_file_window_test()
    prompt_count, answer = run_day8_best_effort_summary_test()
    print("Day 8 agent tuning test passed.")
    print(f"observation_marker={observation_marker}")
    print(f"direct_marker={direct_marker}")
    print(f"prompt_count={prompt_count}")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
