from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.cli_output import stream_to_terminal
from codebase_copilot.llm import LLMSettings, OpenAICompatibleChatSynthesizer
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


class _StreamingResponse:
    def __init__(self, lines: list[str]) -> None:
        self._lines = [line.encode("utf-8") for line in lines]

    def __iter__(self):
        return iter(self._lines)

    def __enter__(self) -> "_StreamingResponse":
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
        "def main() -> str:\n"
        '    return "ok"\n'
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main())\n",
    )


def run_day10_generate_stream_test() -> tuple[str, str]:
    settings = LLMSettings(
        api_key="test-key",
        base_url="https://example.com/v1",
        model="qwen3.5-122b-a10b",
        timeout_seconds=5.0,
    )
    synthesizer = OpenAICompatibleChatSynthesizer(settings)
    captured: dict[str, object] = {}

    def _fake_urlopen(api_request, timeout):
        captured["url"] = api_request.full_url
        captured["body"] = json.loads(api_request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _StreamingResponse(
            [
                'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
                'data: {"choices":[{"delta":{"content":" world"}}]}\n',
                "data: [DONE]\n",
            ]
        )

    with patch("codebase_copilot.llm.request.urlopen", side_effect=_fake_urlopen):
        chunks = list(synthesizer.generate_stream("stream this answer"))

    assert chunks == ["Hello", " world"]
    assert captured["url"] == "https://example.com/v1/chat/completions"
    assert captured["timeout"] == 5.0
    assert captured["body"]["stream"] is True

    sink = StringIO()
    rendered = stream_to_terminal(chunks, stream=sink, prefix="[Final] Answer:\n")
    assert rendered == "Hello world"
    assert sink.getvalue() == "[Final] Answer:\nHello world\n"

    return rendered, str(captured["url"])


def run_day10_agent_streaming_test() -> tuple[str, int]:
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
        prompts: list[dict[str, object]] = []
        steps_seen: list[str] = []

        def _fake_urlopen(api_request, timeout):
            body = json.loads(api_request.data.decode("utf-8"))
            prompts.append(body)
            if body.get("stream") is True:
                return _StreamingResponse(
                    [
                        'data: {"choices":[{"delta":{"content":"Streamed final"}}]}\n',
                        'data: {"choices":[{"delta":{"content":" answer."}}]}\n',
                        "data: [DONE]\n",
                    ]
                )
            return _FakeResponse(
                "<thought>I should search for the entry point first.</thought>\n"
                '<tool_call>{"name":"search_codebase","arguments":{"query":"application entry point main function","top_k":3}}</tool_call>'
                if len(prompts) == 1
                else "<thought>I have enough evidence to answer now.</thought>\n"
                "<final_answer>The entry point is src/app.py and it defines main().</final_answer>"
            )

        def _step_callback(step) -> None:
            if step.action is not None:
                steps_seen.append(step.action)

        rendered_chunks: list[str] = []

        def _stream_handler(chunks) -> str:
            text = "".join(chunks)
            rendered_chunks.append(text)
            return text

        with patch("codebase_copilot.llm.request.urlopen", side_effect=_fake_urlopen):
            result = agent.agent_run(
                "Where is the application entry point?",
                answer_mode="llm",
                max_steps=4,
                step_callback=_step_callback,
                stream_handler=_stream_handler,
            )

        assert result.backend == "llm"
        assert rendered_chunks == ["Streamed final answer."]
        assert result.answer == "Streamed final answer."
        assert len(result.steps) == 1
        assert steps_seen and steps_seen[0].startswith("search_codebase(")
        assert len(prompts) == 3
        assert prompts[2]["stream"] is True
        assert "Draft Final Answer:" in prompts[2]["messages"][0]["content"]
        assert "src/app.py" in prompts[2]["messages"][0]["content"]

        return result.answer, len(result.steps)


def test_day10_llm_streaming() -> None:
    run_day10_generate_stream_test()
    run_day10_agent_streaming_test()


def main() -> int:
    rendered, url = run_day10_generate_stream_test()
    answer, step_count = run_day10_agent_streaming_test()
    print("Day 10 llm streaming test passed.")
    print(f"rendered={rendered}")
    print(f"url={url}")
    print(f"answer={answer}")
    print(f"step_count={step_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
