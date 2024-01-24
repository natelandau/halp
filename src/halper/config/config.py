"""Instantiate Configuration class and set default values."""

from typing import ClassVar

from confz import BaseConfig, ConfigSources, FileSource
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
    categories: dict[str, CategoryConfig] = None
    command_name_ignore_regex: str = ""
    file_exclude_regex: str = ""
    file_globs: tuple[str, ...] = ()
    uncategorized_name: str = "uncategorized"

    CONFIG_SOURCES: ClassVar[ConfigSources | None] = FileSource(file=CONFIG_PATH)
