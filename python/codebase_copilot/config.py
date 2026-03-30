from __future__ import annotations

DEFAULT_CHUNK_SIZE = 120
DEFAULT_CHUNK_OVERLAP = 30

DEFAULT_LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_LLM_MODEL = "qwen3.5-122b-a10b"
DEFAULT_LLM_TIMEOUT_SECONDS = 60.0
DEFAULT_LLM_TEMPERATURE = 0.1
DEFAULT_LLM_MAX_OUTPUT_TOKENS = 1024

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