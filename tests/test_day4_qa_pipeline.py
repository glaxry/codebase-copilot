from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from codebase_copilot.agent import CodebaseQAAgent
from codebase_copilot.pipeline import build_index


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


def run_day4_qa_pipeline_test() -> list[str]:
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
        agent = CodebaseQAAgent.from_metadata(metadata_path)

        expectations = {
            "Where is the application entry point?": ("src/app.py", "def main"),
            "Which file validates username and password?": ("src/auth_service.py", "login_user"),
            "How is token configuration loaded?": ("src/config.py", "TOKEN_TTL"),
            "Which file issues the token?": ("src/auth_service.py", "token_ttl"),
        }

        validated_paths: list[str] = []
        for query, (expected_path, answer_hint) in expectations.items():
            result = agent.ask(query, top_k=3)
            assert result.sources
            assert result.sources[0].chunk.relative_path == expected_path
            assert expected_path in result.answer
            assert answer_hint in result.answer
            assert query in result.prompt
            validated_paths.append(expected_path)

        return validated_paths


def test_day4_qa_pipeline() -> None:
    run_day4_qa_pipeline_test()


def main() -> int:
    validated_paths = run_day4_qa_pipeline_test()
    print("Day 4 QA pipeline test passed.")
    for path in validated_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())