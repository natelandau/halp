"""Utility functions for halper."""

from .printer import console, pp  # isort: skip
from .config import settings, validate_settings  # isort: skip
from .database import db_clear_table_data, db_tables_have_data, init_database
from .mankier import get_mankier_table
from .utilities import check_python_version, get_tldr_command, strip_last_two_lines

__all__ = [
    "check_python_version",
    "console",
    "db_clear_table_data",
    "db_tables_have_data",
    "get_mankier_table",
    "get_tldr_command",
    "init_database",
    "pp",
    "settings",
    "strip_last_two_lines",
    "validate_settings",
]
