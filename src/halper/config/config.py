"""Instantiate Configuration class and set default values."""

from confz import BaseConfig, FileSource
from pydantic import BaseModel

from halper.constants import CONFIG_PATH


class CategoryConfig(BaseModel):
    """Category type."""

    name: str = ""
    code_regex: str = ""
    comment_regex: str = ""
    description: str = ""
    command_name_regex: str = ""
    path_regex: str = ""


class HalpConfig(BaseConfig):  # type: ignore [misc]
    """Halper Configuration."""

    case_sensitive: bool = False
    command_name_ignore_regex: str = ""
    file_exclude_regex: str = ""
    file_globs: tuple[str, ...] = ()
    categories: dict[str, CategoryConfig] = None

    CONFIG_SOURCES = FileSource(file=CONFIG_PATH)
