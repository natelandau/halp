"""Constants for Halp."""

import os
from enum import Enum
from pathlib import Path

import typer
from peewee import SqliteDatabase


class CommentPlacement(str, Enum):
    """Comment placement for halp."""

    ABOVE = "above"
    INLINE = "inline"
    BEST = "best"


class CommandType(str, Enum):
    """Command types for halp."""

    ALIAS = "alias"
    FUNCTION = "function"
    SCRIPT = "script"
    EXPORT = "export"


class ShellType(str, Enum):
    """Shell types for halp."""

    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"
    POWERSHELL = "powershell"
    SH = "sh"


class SearchType(str, Enum):
    """Search types used for the search command."""

    CODE = "code"
    NAME = "name"


CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", "~/.config")).expanduser().absolute() / "halp"
DATA_DIR = Path(os.getenv("XDG_DATA_HOME", "~/.local/share")).expanduser().absolute() / "halp"
STATE_DIR = Path(os.getenv("XDG_STATE_HOME", "~/.local/state")).expanduser().absolute() / "halp"
CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", "~/.cache")).expanduser().absolute() / "halp"
CONFIG_PATH = CONFIG_DIR / "config.toml"
DB_PATH = DATA_DIR / "halp.sqlite"


APP_DIR = Path(typer.get_app_dir("halp"))
# CONFIG_PATH = APP_DIR / "config.toml"  # noqa: ERA001
# DB_PATH = APP_DIR / "halp.sqlite"  # noqa: ERA001
DB = SqliteDatabase(DB_PATH)
VERSION = "0.1.0"
