"""Index subcommand."""

import cappa

from halper.constants import PrintLevel
from halper.controllers import Indexer
from halper.halp import Halp, IndexCommand
from halper.views import index_command_view

from .helpers import initialize_subcommand


def index_command(halp: Halp, cmd: IndexCommand) -> None:
    """Index subcommand.

    Raises:
        cappa.Exit: Exit with code 1 if Python version check fails, no commands are indexed, or with code 0 after successful command execution
    """
    initialize_subcommand(halp=halp, subcommand=cmd, require_db_content=False)

    indexer = Indexer(rebuild=cmd.rebuild)
    indexer.do_index()
    index_command_view(indexer.result, show_all_files=halp.verbosity != PrintLevel.INFO)

    raise cappa.Exit(code=0)
