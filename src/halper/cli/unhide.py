"""Hide subcommand."""

import cappa
from peewee import DoesNotExist

from halper.halp import Halp, UnhideCommand
from halper.models import Command
from halper.utils import pp

from .helpers import initialize_subcommand


def unhide_command(halp: Halp, cmd: UnhideCommand) -> None:
    """Unhide subcommand."""  # noqa: DOC501
    initialize_subcommand(halp=halp, subcommand=cmd, require_db_content=False)

    try:
        commands = [int(x) for x in cmd.commands]
    except ValueError as e:
        pp.error(f"All commands must be integers: {', '.join(cmd.commands)}")
        pp.info("Exiting...")
        raise cappa.Exit(code=1) from e

    for db_id in commands:
        try:
            command = Command.get(db_id)
        except DoesNotExist as e:
            pp.error(f"Command not found: {db_id}")
            pp.info("Exiting...")
            raise cappa.Exit(code=1) from e

        command.hidden = False
        command.save()

        pp.success(f"Unhide {command.name} (#{command.id})")

    pp.info(":rocket: Done!")
    raise cappa.Exit(code=0)
