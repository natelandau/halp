"""Instantiate Configuration class and set default values."""

from typing import Annotated, ClassVar

from confz import BaseConfig, ConfigSources, FileSource
from pydantic import AfterValidator, BaseModel, BeforeValidator

from halper.constants import CONFIG_PATH, CommentPlacement


def valid_comment_placement(value: str) -> CommentPlacement:
    """Convert a string to a CommentPlacement enum."""
    return CommentPlacement(value)


class CategoryConfig(BaseModel):
    """Category type."""

    name: str = ""
    code_regex: str = ""
    comment_regex: str = ""
    description: str = ""
    command_name_regex: str = ""
    path_regex: str = ""


CP = Annotated[
    CommentPlacement,
    AfterValidator(valid_comment_placement),
    BeforeValidator(lambda x: x.lower()),
]


class HalpConfig(BaseConfig):  # type: ignore [misc]
    """Halper Configuration."""

    case_sensitive: bool = False
    categories: dict[str, CategoryConfig] | None = None
    command_name_ignore_regex: str = ""
    comment_placement: CP = CommentPlacement.BEST
    file_exclude_regex: str = ""
    file_globs: tuple[str, ...] = ()
    uncategorized_name: str = "uncategorized"

    CONFIG_SOURCES: ClassVar[ConfigSources | None] = FileSource(file=CONFIG_PATH)
