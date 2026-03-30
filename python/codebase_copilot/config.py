from __future__ import annotations

DEFAULT_CHUNK_SIZE = 120
DEFAULT_CHUNK_OVERLAP = 30

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c-header",
    ".hpp": "cpp-header",
    ".md": "markdown",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".pytest_cache",
    ".venv",
    ".vendor",
    ".vscode",
    ".vs",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "out",
    "venv",
}

IGNORED_FILE_NAMES = {
    "autumn_project1.md",
}

BINARY_FILE_SUFFIXES = {
    ".bin",
    ".class",
    ".dll",
    ".dylib",
    ".exe",
    ".exp",
    ".gif",
    ".ico",
    ".ilk",
    ".jar",
    ".jpeg",
    ".jpg",
    ".lib",
    ".o",
    ".obj",
    ".pdf",
    ".pdb",
    ".png",
    ".pyc",
    ".pyd",
    ".so",
    ".zip",
}
