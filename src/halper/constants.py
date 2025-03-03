"""Constants for halper."""

import os
from enum import Enum
from pathlib import Path

PACKAGE_NAME = "halp"
CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", "~/.config")).expanduser().absolute() / PACKAGE_NAME
DATA_DIR = Path(os.getenv("XDG_DATA_HOME", "~/.local/share")).expanduser().absolute() / PACKAGE_NAME
STATE_DIR = (
    Path(os.getenv("XDG_STATE_HOME", "~/.local/state")).expanduser().absolute() / PACKAGE_NAME
)
CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", "~/.cache")).expanduser().absolute() / PACKAGE_NAME
PROJECT_ROOT_PATH = Path(__file__).parents[2].absolute()
PACKAGE_ROOT_PATH = Path(__file__).parents[0].absolute()


USER_CONFIG_PATH = CONFIG_DIR / "config.toml"
DEFAULT_CONFIG_PATH = PACKAGE_ROOT_PATH / "default_config.toml"
DB_PATH = DATA_DIR / "halp.sqlite"
VERSION = "0.1.0"
UNCATEGORIZED_NAME = "uncategorized"


class PrintLevel(Enum):
    """Define verbosity levels for console output.

    Use these levels to control the amount of information displayed to users. Higher levels include all information from lower levels plus additional details.
    """

    INFO = 0
    DEBUG = 1
    TRACE = 2


class CommandType(str, Enum):
    """Command types for halp."""

    ALIAS = "alias"
    FUNCTION = "function"
    SCRIPT = "script"
    EXPORT = "export"


class CommentPlacement(str, Enum):
    """Comment placement for halp."""

    ABOVE = "above"
    INLINE = "inline"
    BEST = "best"
