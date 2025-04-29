"""Settings and configuration for halper."""

from pathlib import Path

import cappa
from dynaconf import Dynaconf, ValidationError, Validator
from dynaconf.utils.boxing import DynaBox
from rich.console import Console

from halper.constants import (
    DB_PATH,
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT_PATH,
    USER_CONFIG_PATH,
    CommentPlacement,
)

console = Console()


settings = Dynaconf(
    envvar_prefix="HALP",
    settings_files=[DEFAULT_CONFIG_PATH, USER_CONFIG_PATH, PROJECT_ROOT_PATH / "dev-config.toml"],
    environments=False,
    validators=[
        Validator(
            "db_path",
            default=DB_PATH,
            cast=lambda x: Path(x).expanduser().absolute() if x != ":memory:" else x,
        )
    ],
)

settings.validators.register(
    Validator(
        "comment_placement",
        cast=lambda x: CommentPlacement(x.lower()),
        default=CommentPlacement.BEST,
    ),
    Validator("command_name_ignore_regex", cast=str, default=""),
    Validator("file_exclude_regex", cast=str, default=""),
    Validator("file_globs", cast=tuple[str, ...], default=()),
    Validator("categories", cast=dict[str, dict[str, DynaBox]], default={}),
)


def validate_settings() -> Dynaconf:
    """Validate configuration settings against registered validators.

    Validate all registered validators for the Dynaconf settings object. This ensures configuration values meet expected types and constraints before the application runs.

    Args:
        settings (Dynaconf): The Dynaconf settings object to validate

    Returns:
        Dynaconf: The validated settings object

    Raises:
        cappa.Exit: If validation fails, exits with code 1 and prints validation errors
    """
    try:
        settings.validators.validate_all()
    except ValidationError as e:
        accumulative_errors = e.details
        console.print(accumulative_errors)
        raise cappa.Exit(code=1) from e
    except ValueError as e:
        console.print(e)
        raise cappa.Exit(code=1) from e

    return settings
