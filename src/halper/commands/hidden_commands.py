"""Hide a command by ID."""

import typer
from loguru import logger

from halper.models import Command
from halper.utils import console
from halper.views import command_list_table


def list_hidden_commands(full_output: bool = False, only_exports: bool = False) -> None:
    """List all hidden commands."""
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
    """Unhide a command by ID."""
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
    """Hide a command by ID."""
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
