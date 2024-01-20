"""Constants for Halp."""

from enum import Enum
from pathlib import Path

import typer
from peewee import SqliteDatabase

from halper.config import Config


class CommandType(Enum):
    """Command types for halp."""

    ALIAS = "alias"
    FUNCTION = "function"
    SCRIPT = "script"
    EXPORT = "export"


class ShellType(Enum):
    """Shell types for halp."""

    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"
    POWERSHELL = "powershell"
    SH = "sh"


APP_DIR = Path(typer.get_app_dir("halp"))
CONFIG = Config(config_path=APP_DIR / "config.toml")
DB_PATH = APP_DIR / "halp.sqlite"
DB = SqliteDatabase(DB_PATH)
UNKNOWN_CATEGORY_NAME = "Uncategorized"
