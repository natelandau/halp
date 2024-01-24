"""Display individual commands."""

import contextlib
import sys

import peewee
import sh
import typer
from loguru import logger

from halper.constants import CommandType
from halper.models import Command
from halper.utils import console, errors, get_mankier_table, get_tldr_command
from halper.views import command_list_table, display_commands, strings_to_columns


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
        else:
            query = query.where(
                Command.command_type != CommandType.EXPORT.name,
                Command.hidden == False,  # noqa: E712
            )

        if full_output:
            table = command_list_table(
                commands=query.order_by(Command.name),
                full_output=full_output,
                only_exports=only_exports,
                show_categories=True,
            )
            console.print(table)
            raise typer.Exit()

        command_names = [command.name for command in query.order_by(Command.name)]
        if not command_names:
            console.print("No commands found")
            raise typer.Exit(1)

        columns = strings_to_columns(name="command", strings=command_names)
        console.print(columns)

    except peewee.PeeweeException as e:
        logger.exception(f"Error fetching commands: {e}")
        raise typer.Exit(code=1) from e

    raise typer.Exit()


def command_display(input_string: str, full_output: bool = False) -> None:
    """Display an individual command's information from indexed commands or using 'tldr' if available.

    Args:
        input_string: The command name to display information about.
        full_output: Whether to display full command information.

    Raises:
        typer.Exit: Exits the application with status code 0 on success, 1 on failure.
    """
    # Check if input_string contains a space
    if " " in input_string:
        try:
            console.print(get_mankier_table(input_string))
            raise typer.Exit()
        except errors.MankierCommandNotFoundError:
            input_string = input_string.split(" ")[0]

    tldr = get_tldr_command()

    # Attempt to find the command in the database
    try:
        commands = Command.select().where(Command.name == input_string, Command.hidden == False)  # noqa: E712

        # Check if commands were found in the database
        if commands:
            found_in_tldr = False
            if tldr:
                with contextlib.suppress(sh.ErrorReturnCode):
                    tldr(input_string)
                    found_in_tldr = True

            display_commands(commands, input_string, full_output, found_in_tldr)
            raise typer.Exit()

        # Attempt to display using tldr if installed
        if tldr:
            with contextlib.suppress(sh.ErrorReturnCode):
                tldr(input_string, _out=sys.stdout, _err=sys.stderr)
                raise typer.Exit()

    except peewee.PeeweeException as e:
        console.print(f"Error accessing the database: {e}")
        raise typer.Exit(1) from e

    console.print(f"No command found matching: [code]{input_string}[/code]")
    raise typer.Exit(1)
