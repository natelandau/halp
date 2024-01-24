"""Shared utilities for Halp."""

from .console import console  # isort:skip
from .logging import InterceptHandler, instantiate_logger  # isort:skip

from .helpers import (
    check_python_version,
    edit_config,
    get_tldr_command,
    strip_last_two_lines,
    validate_config,
)
from .mankier import get_mankier_table

__all__ = [
    "InterceptHandler",
    "check_python_version",
    "console",
    "edit_config",
    "get_mankier_table",
    "get_tldr_command",
    "instantiate_logger",
    "strip_last_two_lines",
    "validate_config",
]
