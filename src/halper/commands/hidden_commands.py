"""Hide a command by ID."""

import typer
from loguru import logger

from halper.models import Command
from halper.utils import console
from halper.views import command_list_table


def list_hidden_commands(full_output: bool = False, only_exports: bool = False) -> None:
    """Display a table of all commands marked as hidden.

    Show a formatted table listing all commands that have been hidden from normal search results.
    The table includes command details like name, description, and categories. This helps users
    review and manage which commands they have chosen to hide.

    Args:
        full_output: bool - Whether to show full command details including code. Defaults to False.
        only_exports: bool - Whether to only show exported commands. Defaults to False.

    Raises:
        typer.Exit: Always exits after displaying table. Exit code 0 indicates success.
    """
    commands = Command.select().where(Command.hidden == True).order_by(Command.name)  # noqa: E712
    if not commands:
        console.print("No hidden commands")
        raise typer.Exit(code=0)

    table = command_list_table(
        commands=commands,
        full_output=full_output,
        only_exports=only_exports,
        show_hidden=True,
        show_categories=True,
        title="Hidden Commands",
    )
    console.print(table)

    raise typer.Exit(code=0)


def unhide_commands(command_ids: str | None = None) -> None:
    """Make previously hidden commands visible again by their IDs.

    Take a comma-separated string of command IDs and make those commands visible in the command list
    again by setting their hidden flag to False. This allows restoring commands that were previously
    hidden from view.

    Args:
        command_ids: str | None - Comma-separated string of command IDs to unhide (e.g. "1,2,3").
            If None or invalid, exits with error.

    Raises:
        typer.Exit: If command_ids is None/invalid, any ID is not an integer, or command not found.
            Exit code 1 indicates error, 0 indicates success.

    Example:
        unhide_commands("1,5,10")  # Makes commands with IDs 1, 5 and 10 visible again
    """
    if not command_ids or not isinstance(command_ids, str):
        console.print("No command ID provided")
        raise typer.Exit(code=1)

    for command_id in command_ids.split(","):
        try:
            idx = int(command_id)
        except ValueError as e:
            logger.error(f"Invalid command ID: {command_id}")
            raise typer.Exit(code=1) from e

        try:
            command = Command.get_by_id(idx)
            command.hidden = False
            command.save()
            console.print(f"Command {command.name} unhidden")
        except Command.DoesNotExist as e:
            console.print(f"Command with ID {idx} not found")
            raise typer.Exit(code=1) from e

    raise typer.Exit(code=0)


def hide_commands(command_ids: str | None = None) -> None:
    """Hide specified commands from appearing in command listings.

    Take a comma-separated string of command IDs and hide those commands from appearing in command
    listings by setting their hidden flag to True. This allows removing commands from view without
    deleting them from the database, useful for decluttering the command list or hiding deprecated
    commands while preserving them.

    Args:
        command_ids: str | None - Comma-separated string of command IDs to hide (e.g. "1,2,3").
            If None or invalid, exits with error.

    Raises:
        typer.Exit: If command_ids is None/invalid, any ID is not an integer, or command not found.
            Exit code 1 indicates error, 0 indicates success.

    Example:
        hide_commands("1,5,10")  # Hides commands with IDs 1, 5 and 10 from listings
    """
    if not command_ids or not isinstance(command_ids, str):
        console.print("No command ID provided")
        raise typer.Exit(code=1)

    for command_id in command_ids.split(","):
        try:
            idx = int(command_id)
        except ValueError as e:
            logger.error(f"Invalid command ID: {command_id}")
            raise typer.Exit(code=1) from e

        try:
            command = Command.get_by_id(idx)
            command.hidden = True
            command.save()
            console.print(f"Command {command.name} hidden")
        except Command.DoesNotExist as e:
            console.print(f"Command with ID {idx} not found")
            raise typer.Exit(code=1) from e

    raise typer.Exit(code=0)
