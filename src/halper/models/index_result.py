"""Representation of the result of the Indexer."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class IndexResult:
    """Result of the Indexer."""

    categories: list[str] = field(default_factory=list)
    glob_paths: dict[str, int] = field(default_factory=dict)
    files: dict[Path, int] = field(default_factory=dict)
    total_commands: int = 0
