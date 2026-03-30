from __future__ import annotations

from pathlib import Path

from .config import BINARY_FILE_SUFFIXES, IGNORED_DIRECTORIES, SUPPORTED_EXTENSIONS
from .models import RepoFile


class RepositoryLoader:
    """Load supported source files from a repository while skipping noisy paths."""

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root).resolve()
        if not self.repo_root.exists() or not self.repo_root.is_dir():
            raise ValueError(f"Repository path is invalid: {self.repo_root}")

    def iter_file_paths(self) -> list[Path]:
        file_paths: list[Path] = []
        for path in self.repo_root.rglob("*"):
            if not path.is_file():
                continue
            if self._should_skip(path):
                continue
            file_paths.append(path)
        return sorted(file_paths)

    def load_files(self) -> list[RepoFile]:
        repo_files: list[RepoFile] = []
        for path in self.iter_file_paths():
            content = self._read_text(path)
            if content is None:
                continue

            relative_path = path.relative_to(self.repo_root).as_posix()
            repo_files.append(
                RepoFile(
                    relative_path=relative_path,
                    absolute_path=str(path),
                    language=SUPPORTED_EXTENSIONS[path.suffix.lower()],
                    content=content,
                )
            )
        return repo_files

    def _should_skip(self, path: Path) -> bool:
        relative_parts = path.relative_to(self.repo_root).parts
        if any(part in IGNORED_DIRECTORIES for part in relative_parts[:-1]):
            return True

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            return True
        if suffix in BINARY_FILE_SUFFIXES:
            return True
        return False

    @staticmethod
    def _read_text(path: Path) -> str | None:
        data = path.read_bytes()
        if b"\x00" in data:
            return None

        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return None
