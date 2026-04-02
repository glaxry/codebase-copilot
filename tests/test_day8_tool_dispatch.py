from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.pipeline import build_index
from codebase_copilot.tools import list_files, read_file, search_codebase


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_demo_repo(repo_root: Path) -> None:
    _write_text(
        repo_root / "src" / "app.py",
        "from auth_service import login_user\n\n"
        "def main() -> str:\n"
        '    return login_user("demo", "secret", {"token_ttl": "3600"})\n',
    )
    _write_text(
        repo_root / "src" / "auth_service.py",
        "def login_user(username: str, password: str, config: dict[str, str]) -> str:\n"
        "    if not username or not password:\n"
        '        raise ValueError("username and password are required")\n'
        '    return f"{username}:{config[\'token_ttl\']}"\n',
    )
    _write_text(
        repo_root / "docs" / "notes.md",
        "# Notes\n\nUse source files as the ground truth.\n",
    )


def run_day8_tool_dispatch_test() -> tuple[str, str, str]:
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
        agent = CodebaseQAAgent.from_metadata(metadata_path)

        search_output = search_codebase(agent.retrieve, "application entry point", top_k=2)
        assert "[src/app.py lines " in search_output
        assert "def main()" in search_output

        read_output = read_file(repo_root, "src/app.py", start_line=1, end_line=10)
        assert "[src/app.py lines 1-" in read_output
        assert "def main()" in read_output

        file_output = list_files(repo_root, "*.py")
        assert "src/app.py" in file_output
        assert "src/auth_service.py" in file_output
        assert "docs/notes.md" not in file_output

        blocked = read_file(repo_root, "../README.md")
        assert "error=path escapes repo root" in blocked

        return "search_codebase", "read_file", "list_files"


def test_day8_tool_dispatch() -> None:
    run_day8_tool_dispatch_test()


def main() -> int:
    tools = run_day8_tool_dispatch_test()
    print("Day 8 tool dispatch test passed.")
    for tool in tools:
        print(tool)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
