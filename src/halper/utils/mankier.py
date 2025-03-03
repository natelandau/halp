"""Interact with mankier.com."""

import cappa
import httpx
from markdownify import markdownify as md
from rich.markdown import Markdown
from rich.table import Table

from . import errors
from .printer import pp
from .utilities import strip_last_two_lines


def get_mankier_table(input_text: str) -> Table:  # pragma: no cover
    """Display an individual command's information from mankier.com.

    Args:
        input_text (str): The command to get the information for.

    Returns:
        Table: A rich Table object.
    """
    grid = Table.grid(expand=False, padding=(0, 1))
    grid.add_column(style="bold")
    grid.add_column()

    description = get_mankier_description(input_text)
    explanation = get_mankier_explanation(input_text)

    grid.add_row("Command:", f"[bold]{input_text}[/bold]")
    grid.add_row("Description:", Markdown(description))
    grid.add_row("Explanation:", explanation)

    return grid


def get_mankier_description(input_string: str) -> str:  # pragma: no cover
    """Query mankier.com for a command's description.

    Args:
        input_string (str): The command to get the description for.

    Returns:
        str: A string containing the command's description.

    Raises:
        cappa.Exit: If there is an error contacting mankier.com.
        errors.MankierCommandNotFoundError: If the command is not found on mankier.com.
    """
    # Get the command description as markdown
    url = f"https://www.mankier.com/api/v2/mans/{input_string.split(' ')[0]}.1/sections/Description"

    try:
        response = httpx.get(url, timeout=15)
    except Exception as e:
        raise cappa.Exit(code=1) from e

    if response.status_code != 200:  # noqa: PLR2004
        pp.error(f"Error contacting mankier.com: {response.status_code}")
        raise cappa.Exit(code=1)

    if "html" not in response.json():
        raise errors.MankierCommandNotFoundError(input_string)

    converted_to_markdown = md(response.json()["html"])
    return "\n".join(converted_to_markdown.splitlines()[3:4])


def get_mankier_explanation(input_string: str) -> str:  # pragma: no cover
    """Query mankier.com for a command's explanation.

    Args:
        input_string (str): The command to get the explanation for.

    Returns:
        str: A string containing the command's explanation.

    Raises:
        cappa.Exit: If there is an error contacting mankier.com.
    """
    url = "https://www.mankier.com/api/explain/"
    params = {"q": input_string}

    try:
        response = httpx.get(url, params=params, timeout=15)
    except Exception as e:
        raise cappa.Exit(code=1) from e

    if response.status_code != 200:  # noqa: PLR2004
        pp.error(f"Error contacting mankier.com: {response.status_code}")
        raise cappa.Exit(code=1)

    return strip_last_two_lines(response.text)
