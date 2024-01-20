"""Display individual commands."""

import contextlib
import sys

import peewee
import sh
import typer
from loguru import logger
from rich.columns import Columns

from halper.constants import CommandType
from halper.models import Command
from halper.utils import console, get_tldr_command


def command_list(
    full_output: bool = False,
    only_exports: bool = False,
) -> None:
    """List all commands with options to filter by command type.

    Args:
        full_output: If True, lists all commands. If False, filters out export commands.
        only_exports: If True, lists only export commands.

    Raises:
        typer.Exit: Exits the application with a status code. The status code is 1 if either no commands are found, and 0 upon successful completion.
    """
    try:
        query = Command.select()
        if only_exports:
            query = query.where(
                Command.command_type == CommandType.EXPORT.name,
                Command.hidden == False,  # noqa: E712
            )
        elif not full_output:
            query = query.where(
                Command.command_type != CommandType.EXPORT.name,
                Command.hidden == False,  # noqa: E712
            )

        command_names = [command.name for command in query.order_by(Command.name)]
        if not command_names:
            console.print("No commands found")
            raise typer.Exit(1)

        columns = Columns(
            command_names,
            equal=True,
            expand=True,
            title="[bold underline]All Indexed Commands[/bold underline]",
        )
        console.print(columns)

    except peewee.PeeweeException as e:
        logger.exception(f"Error fetching commands: {e}")
        raise typer.Exit(code=1) from e

    raise typer.Exit()


def command_display(input_string: str, full_output: bool = False) -> None:
    """Display an individual command's information.

    Tries to display information from indexed commands first. If not found,
    it attempts to display using 'tldr' if installed.

    Args:
        input_string: Name of the command to display.
        full_output: Flag to indicate whether to display full output.

    Raises:
        typer.Exit: Exits the application with a status code. The status code is 1 if either no commands are found, and 0 upon successful completion.
    """
    tldr = get_tldr_command()

    try:
        commands = Command.select().where(Command.name == input_string, Command.hidden == False)  # noqa: E712

        if commands:
            found_in_tldr = False
            if tldr:
                with contextlib.suppress(sh.ErrorReturnCode):
                    tldr(input_string)
                    found_in_tldr = True

            show_id = False
            if len(commands) > 1:
                console.print(
                    f"[bold]Found {len(commands)} commands matching:[/bold] [code]{input_string}[/code]"
                )
                show_id = True

            for command in commands:
                if len(commands) > 1:
                    console.rule()

                console.print(
                    command.table(
                        full_output=full_output, found_in_tldr=found_in_tldr, show_id=show_id
                    )
                )
            if len(commands) > 1:
                console.rule()
            raise typer.Exit()

        # If we have tldr installed, try to display it
        if tldr:
            with contextlib.suppress(sh.ErrorReturnCode):
                tldr(input_string, _out=sys.stdout, _err=sys.stderr)
                raise typer.Exit()

    except peewee.PeeweeException as e:
        console.print(f"Error accessing the database: {e}")
        raise typer.Exit(1) from e

    console.print(f"No command found matching: [code]{input_string}[/code]")
    raise typer.Exit(1)
