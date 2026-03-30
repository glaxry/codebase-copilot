from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoFile:
    relative_path: str
    absolute_path: str
    language: str
    content: str

    @property
    def line_count(self) -> int:
        return len(self.content.splitlines())
