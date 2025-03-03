"""Hide subcommand."""

import cappa
from peewee import DoesNotExist

from halper.halp import Halp, HideCommand
from halper.models import Command
from halper.utils import pp

from .helpers import initialize_subcommand


def hide_command(halp: Halp, cmd: HideCommand) -> None:
    """Hide subcommand."""  # noqa: DOC501
    initialize_subcommand(halp=halp, subcommand=cmd, require_db_content=False)

    try:
        commands = [int(x) for x in cmd.commands]
    except ValueError as e:
        pp.error(f"All commands must be integers: {', '.join(cmd.commands)}")
        raise cappa.Exit(code=1) from e

    for db_id in commands:
        try:
            command = Command.get(db_id)
        except DoesNotExist as e:
            pp.error(f"Command not found: {db_id}")
            raise cappa.Exit(code=1) from e

        command.hidden = True
        command.save()

        pp.success(f"Hide {command.name} (#{command.id})")

    pp.notice("Done!")
    raise cappa.Exit(code=0)
