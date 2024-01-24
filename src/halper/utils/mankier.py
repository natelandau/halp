"""Interact with mankier.com."""

import requests
import typer
from loguru import logger
from markdownify import markdownify as md
from rich.markdown import Markdown
from rich.table import Table

from halper.utils import errors, strip_last_two_lines


def get_mankier_table(input_text: str) -> Table:
    """Display an individual command's information from mankier.com."""
    grid = Table.grid(expand=False, padding=(0, 1))
    grid.add_column(style="bold")
    grid.add_column()

    description = get_mankier_description(input_text)
    explanation = get_mankier_explanation(input_text)

    grid.add_row("Command:", f"[bold]{input_text}[/bold]")
    grid.add_row("Description:", Markdown(description))
    grid.add_row("Explanation:", explanation)

    return grid


def get_mankier_description(input_string: str) -> str:
    """Query mankier.com for a command's description."""
    # Get the command description as markdown
    url = f"https://www.mankier.com/api/v2/mans/{input_string.split(' ')[0]}.1/sections/Description"

    try:
        response = requests.get(url, timeout=15)
    except Exception as e:  # noqa: BLE001
        raise typer.Exit(1) from e

    if response.status_code != 200:  # noqa: PLR2004
        logger.error(f"Error contacting mankier.com: {response.status_code} {response.reason}")
        raise typer.Exit(1)

    if "html" not in response.json():
        raise errors.MankierCommandNotFoundError(input_string)

    converted_to_markdown = md(response.json()["html"])
    return "\n".join(converted_to_markdown.splitlines()[3:4])


def get_mankier_explanation(input_string: str) -> str:
    """Query mankier.com for a command's explanation."""
    url = "https://www.mankier.com/api/explain/"
    params = {"q": input_string}

    try:
        response = requests.get(url, params=params, timeout=15)
    except Exception as e:  # noqa: BLE001
        raise typer.Exit(1) from e

    if response.status_code != 200:  # noqa: PLR2004
        logger.error(f"Error contacting mankier.com: {response.status_code} {response.reason}")
        raise typer.Exit(1)

    return strip_last_two_lines(response.text)
