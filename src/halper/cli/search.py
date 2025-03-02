"""Search subcommand."""

import contextlib
import sys

import cappa
import sh
from peewee import PeeweeException, fn

from halper.halp import Halp, SearchCommand
from halper.models import Command
from halper.utils import (
    console,
    errors,
    get_mankier_table,
    get_tldr_command,
    pp,
)
from halper.views import command_detail_view

from .helpers import initialize_subcommand


def search_command(halp: Halp, cmd: SearchCommand) -> None:
    """Search subcommand.

    Raises:
        cappa.Exit: Exit with code 1 if Python version check fails, no commands are indexed, or with code 0 after successful command execution
    """
    initialize_subcommand(halp=halp, subcommand=cmd, require_db_content=True)

    # The database of commands and tldr pages only contains commands without arguments. We check the online help database from mankier for commands with arguments to print contextually relevant information.
    if " " in cmd.input_string:
        try:
            console.print(get_mankier_table(cmd.input_string))
            raise cappa.Exit()
        except errors.MankierCommandNotFoundError:
            (cmd.input_string) = cmd.input_string.split(" ")[0]

    search_field = Command.name if not cmd.search_code else Command.code

    try:
        if not cmd.regex and not cmd.search_code:
            db_commands = Command.select().where(
                Command.name == cmd.input_string, Command.hidden == cmd.show_hidden
            )
        else:
            db_commands = Command.select().where(
                fn.REGEXP(cmd.input_string, search_field), Command.hidden == cmd.show_hidden
            )
    except PeeweeException as e:
        pp.error(f"Error accessing the database: {e}")
        raise cappa.Exit(code=1) from e

    found_in_tldr = False
    if tldr := get_tldr_command():  # pragma: no cover
        with contextlib.suppress(sh.ErrorReturnCode):
            tldr(cmd.input_string)
            found_in_tldr = True

    if db_commands:
        command_detail_view(
            commands=db_commands, input_string=cmd.input_string, found_in_tldr=found_in_tldr
        )
        raise cappa.Exit(code=0)

    if tldr:  # pragma: no cover
        with contextlib.suppress(sh.ErrorReturnCode):
            tldr(cmd.input_string, _out=sys.stdout, _err=sys.stderr)
            raise cappa.Exit(code=0)

    pp.error(f"No command found matching: [code]{cmd.input_string}[/code]")
    raise cappa.Exit(code=1)
