"""Helper functions for the halp package."""

import shutil
import sys
from pathlib import Path

import sh
import typer
from confz import validate_all_configs
from loguru import logger
from pydantic import ValidationError

from halper.config import HalpConfig
from halper.constants import CONFIG_PATH

from .console import console


def strip_last_two_lines(multiline_string: str) -> str:
    r"""Remove the last line from a multiline string.

    Splits the string into lines, removes the last line, and rejoins the remaining lines.

    Args:
        multiline_string (str): The multiline string to process.

    Returns:
        str: The modified string with the last line removed.

    Example:
        >>> example_string = "Line 1\nLine 2\nLine 3"
        >>> strip_last_two_lines(example_string)
        'Line 1'
    """
    # Split the string into lines
    lines = multiline_string.splitlines()

    # Remove the last line and rejoin the remaining lines
    return "\n".join(lines[:-2])


def get_tldr_command() -> sh.Command | None:
    """Get the 'tldr' command if available.

    Returns:
        An instance of sh.Command configured for 'tldr' if available,
        otherwise None.
    """
    try:
        tldr_path = sh.which("tldr").strip()
        return sh.Command(tldr_path).bake("-q")
    except sh.ErrorReturnCode:
        return None


def check_python_version() -> bool:
    """Check the Python version.

    Returns:
        bool: True if the Python version is >= 3.9, False otherwise.
    """
    return sys.version_info >= (3, 10)


def create_default_config() -> None:
    """Create a default configuration file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    default_config_file = Path(__file__).parent.parent / "default_config.toml"
    shutil.copy(default_config_file, CONFIG_PATH)

    msg = """\
[bold]halp requires a configuration file to run[/bold]
Empty configuration created, edit before continuing
"""
    console.print(msg)
    edit_config(exit_code=1)


def edit_config(exit_code: int = 0) -> None:
    """Edit the configuration file."""
    if not CONFIG_PATH.exists():
        create_default_config()

    msg = f"""\
Config location: '{CONFIG_PATH}'
[dim]Attempting to open file...[/dim]"""
    console.print(msg)
    typer.launch(str(CONFIG_PATH), locate=True)
    raise typer.Exit(code=exit_code)


def validate_config() -> None:
    """Validate the configuration file.

    Returns:
        bool: True if the configuration file is valid, False otherwise.
    """
    # Create a default configuration file if one does not exist
    if not CONFIG_PATH.exists():
        create_default_config()

    try:
        validate_all_configs()
    except ValidationError as e:
        logger.error(f"Invalid configuration file: {CONFIG_PATH}")
        for error in e.errors():
            console.print(f"           [red]{error['loc'][0]}: {error['msg']}[/red]")

        raise typer.Exit(code=1) from e

    # Confirm we don't have a default configuration file
    if (
        not HalpConfig().file_globs
        and not HalpConfig().file_exclude_regex
        and not HalpConfig().categories
    ):
        console.print(
            "Configuration file is using default values. Please edit the file before continuing.\nRun [code]halp --edit-config[/code] to open the file."
        )
        raise typer.Exit(code=1)
