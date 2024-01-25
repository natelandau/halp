"""Search for commands by name, description, or code."""

import typer
from peewee import fn

from halper.constants import CommandType, SearchType
from halper.models import Command
from halper.utils import console
from halper.views import command_list_table


def search_commands(
    search_type: SearchType, pattern: str | None, full_output: bool = False
) -> None:
    """Search for commands based on a given pattern and type.

    Args:
        search_type (SearchType): The type of search, either 'CODE' or 'NAME'.
        pattern (str): The regex pattern to search for.
        full_output (bool, optional): Flag to determine the verbosity of output. Defaults to False.

    Raises:
        typer.Exit: Exits the application if no matching commands are found.
    """
    if not pattern:
        console.print("No search pattern provided.")
        raise typer.Exit(1)

    search_field = Command.name if search_type == SearchType.NAME else Command.code
    commands = Command.select().where(
        fn.REGEXP(pattern, search_field), Command.command_type != CommandType.EXPORT.name
    )

    if not commands.exists():
        console.print(f"No commands found matching regex: [code]{pattern}[/code]")
        raise typer.Exit(1)

    result = command_list_table(
        commands=commands, full_output=full_output, show_categories=full_output
    )
    console.print(result)
    raise typer.Exit()
