from __future__ import annotations

import subprocess
import sys
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from codebase_copilot.cli_output import format_final_label, render_agent_output, render_agent_step, supports_color
from codebase_copilot.models import AgentRunResult, AgentStep, CodeChunk


ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = ROOT / "python" / "main.py"


class _TTYBuffer(StringIO):
    def __init__(self, *, is_tty: bool) -> None:
        super().__init__()
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


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


def run_day10_terminal_render_test() -> tuple[str, str]:
    tty_stream = _TTYBuffer(is_tty=True)
    pipe_stream = _TTYBuffer(is_tty=False)
    assert supports_color(tty_stream) is True
    assert supports_color(pipe_stream) is False

    step = AgentStep(
        step_number=1,
        thought="Search first.",
        action="search_codebase(query='entry point')",
        observation="[src/app.py lines 1-6]\ndef main() -> str:",
    )
    step_lines = render_agent_step(step, preview_lines=3, use_color=True)
    assert "\x1b[34m" in step_lines[0]
    assert "\x1b[32m" in step_lines[1]
    assert "\x1b[33m" in step_lines[2]

    chunk = CodeChunk(
        chunk_id=1,
        relative_path="src/app.py",
        language="python",
        start_line=1,
        end_line=6,
        text='def main() -> str:\n    return "ok"',
    )
    result = AgentRunResult(
        query="Where is the application entry point?",
        answer="The entry point is src/app.py.",
        prompt="prompt text",
        steps=[step],
        backend="local",
    )
    rendered = render_agent_output(result, preview_lines=3, show_prompt=False, use_color=True)
    assert format_final_label(True) in rendered

    return step_lines[0], rendered


def run_day10_non_tty_output_test() -> str:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        metadata_path = repo_root / "data" / "metadata.json"
        _create_demo_repo(repo_root)

        subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "index",
                "--repo",
                str(repo_root),
                "--output",
                str(metadata_path),
                "--chunk-size",
                "12",
                "--overlap",
                "3",
                "--embedding-dim",
                "128",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(MAIN_SCRIPT),
                "agent",
                "Where is the application entry point?",
                "--index",
                str(metadata_path),
                "--answer-mode",
                "local",
                "--max-steps",
                "4",
                "--no-stream",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        assert "\x1b[" not in completed.stdout
        assert "=== AGENT RESULT ===" in completed.stdout
        return completed.stdout


def test_day10_terminal_polish() -> None:
    run_day10_terminal_render_test()
    run_day10_non_tty_output_test()


def main() -> int:
    step_header, rendered = run_day10_terminal_render_test()
    stdout = run_day10_non_tty_output_test()
    print("Day 10 terminal polish test passed.")
    print(step_header)
    print(rendered.splitlines()[0])
    print(stdout.splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
