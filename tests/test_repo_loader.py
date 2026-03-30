from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from codebase_copilot.repo_loader import RepositoryLoader


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_binary(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00\x01\x02binary")


def run_repo_loader_test() -> list[str]:
    with TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        _write_text(repo_root / "src" / "app.py", "print('hello')\n")
        _write_text(repo_root / "src" / "engine.cpp", "int main() { return 0; }\n")
        _write_text(repo_root / "docs" / "overview.md", "# overview\n")
        _write_text(repo_root / "build" / "ignored.py", "print('ignore')\n")
        _write_text(repo_root / ".git" / "config", "[core]\n")
        _write_binary(repo_root / "src" / "broken.py")
        _write_text(repo_root / "assets" / "logo.png", "not really png\n")

        loader = RepositoryLoader(repo_root)
        files = loader.load_files()
        loaded_paths = [repo_file.relative_path for repo_file in files]

        assert loaded_paths == [
            "docs/overview.md",
            "src/app.py",
            "src/engine.cpp",
        ]
        assert files[0].language == "markdown"
        assert files[1].language == "python"
        assert files[2].language == "cpp"
        assert files[1].line_count == 1

        return loaded_paths


def main() -> int:
    loaded_paths = run_repo_loader_test()
    print("Repository loader test passed.")
    for path in loaded_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
