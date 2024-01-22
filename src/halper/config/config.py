"""Instantiate Configuration class and set default values."""

from confz import BaseConfig, FileSource
from pydantic import BaseModel

from halper.constants import CONFIG_PATH


class CategoryConfig(BaseModel):
    """Category type."""

    category_name: str = ""
    code_regex: str = ""
    comment_regex: str = ""
    description: str = ""
    name_regex: str = ""
    path_regex: str = ""

    def asdict(self) -> dict[str, str]:
        """Convert Category to dictionary."""
        return {
            "name": self.category_name,
            "description": self.description,
            "code_regex": self.code_regex,
            "comment_regex": self.comment_regex,
            "name_regex": self.name_regex,
            "path_regex": self.path_regex,
        }


class HalpConfig(BaseConfig):  # type: ignore [misc]
    """Halper Configuration."""

    case_sensitive: bool = False
    command_name_ignore_regex: str = ""
    file_exclude_regex: str = ""
    file_globs: tuple[str, ...] = ()
    categories: dict[str, CategoryConfig] = None

    CONFIG_SOURCES = FileSource(file=CONFIG_PATH)
