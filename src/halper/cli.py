"""Halp CLI."""

from pathlib import Path
from typing import Annotated, Optional

import peewee
import typer
from loguru import logger

from halper.__version__ import __version__

from halper.utils import console, errors, instantiate_logger, check_python_version  # isort:skip
from halper.commands import (
    category_display,
    command_display,
    command_list,
    hide_commands,
    list_hidden_commands,
    unhide_commands,
)
from halper.constants import APP_DIR, CONFIG, DB, UNKNOWN_CATEGORY_NAME
from halper.models import Database, Indexer

app = typer.Typer(add_completion=False, rich_markup_mode="rich")


typer.rich_utils.STYLE_HELPTEXT = ""


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"halp version: {__version__}")
        raise typer.Exit()


@app.command()
def main(  # noqa: PLR0917, C901
    input_string: Annotated[
        Optional[str],
        typer.Argument(
            help="Command to display", hidden=True, metavar="[COMMAND NAME]", show_default=False
        ),
    ] = None,
    category: Annotated[
        bool,
        typer.Option(
            "--category", "--cat", help="Show commands organized by categories", show_default=False
        ),
    ] = False,
    only_exports: Annotated[
        bool, typer.Option("--exports", help="Filter to only display EXPORTS")
    ] = False,
    full_output: Annotated[
        bool, typer.Option("--full", help="Show additional output", show_default=False)
    ] = False,
    ids_to_hide: Annotated[
        Optional[str],
        typer.Option(
            "--hide",
            help="Hide command(s) by ID. [dim]Use comma separator: --hide 234,456",
            show_default=False,
        ),
    ] = None,
    list_hidden: Annotated[
        bool, typer.Option("--list-hidden", help="List hidden commands", show_default=False)
    ] = False,
    show_list: Annotated[
        bool, typer.Option("--list", help="List names only", show_default=False)
    ] = False,
    uncategorized: Annotated[
        bool, typer.Option("--uncategorized", help="Show uncategorized commands only")
    ] = False,
    ids_to_unhide: Annotated[
        Optional[str],
        typer.Option(
            "--unhide",
            help="Unhide command(s) by ID. [dim]Use comma separator: --unhide 234,456",
            show_default=False,
        ),
    ] = None,
    edit_configuration: Annotated[
        bool,
        typer.Option(
            "--edit-config",
            help="Edit the configuration file",
            show_default=True,
        ),
    ] = False,
    # MAINTENANCE COMMANDS ######################
    index: Annotated[
        bool,
        typer.Option(
            "--index", help="Index files for changes", rich_help_panel="Maintenance Commands"
        ),
    ] = False,
    index_full: Annotated[
        bool,
        typer.Option(
            "--index-full",
            help="Completely rebuild index of commands",
            rich_help_panel="Maintenance Commands",
        ),
    ] = False,
    # OUTPUT SETTINGS ######################
    log_file: Annotated[
        Path,
        typer.Option(
            help="Path to log file",
            show_default=True,
            dir_okay=False,
            file_okay=True,
            exists=False,
            rich_help_panel="Output Settings",
        ),
    ] = Path(f"{APP_DIR}/halp.log"),
    log_to_file: Annotated[
        bool,
        typer.Option(
            "--log-to-file",
            help="Log to file",
            show_default=True,
            rich_help_panel="Output Settings",
        ),
    ] = False,
    verbosity: Annotated[
        int,
        typer.Option(
            "-v",
            "--verbose",
            show_default=True,
            help="""Set verbosity level(0=INFO, 1=DEBUG, 2=TRACE)""",
            count=True,
            rich_help_panel="Output Settings",
        ),
    ] = 0,
    version: Annotated[  # noqa: ARG001
        Optional[bool],
        typer.Option(
            "--version",
            is_eager=True,
            callback=version_callback,
            help="Print version and exit",
            rich_help_panel="Output Settings",
        ),
    ] = None,
) -> None:
    """Your one stop shop for command line help.

    \b
    Point Halp at the appropriate dotfiles and it will index all your custom commands and add them to categories you specify. Then you can query it to find your commands and their usage.
    """  # noqa: D301
    # Instantiate Logging
    instantiate_logger(verbosity, log_file, log_to_file)

    if not check_python_version():
        logger.error("Python version must be >= 3.10")
        raise typer.Exit(code=1)

    # Validate config
    try:
        CONFIG.validate()
    except errors.InvalidConfigError as e:
        logger.error(e)
        raise typer.Abort from e

    # Instantiate Database
    try:
        db = Database(DB)
        db.instantiate()
    except peewee.OperationalError as e:
        logger.exception(f"Unable to instantiate database: {e}")
        raise typer.Exit(code=1) from e

    if db.is_empty() and (not index and not index_full):
        console.print(
            "No commands found.\nMake sure your configuration file is up to date and run [code]halp --index[/code] to index your commands."
        )
        raise typer.Exit(code=1)

    if index or index_full:
        indexer = Indexer(rebuild=index_full)
        indexer.do_index()
        raise typer.Exit(0)

    if edit_configuration:
        CONFIG.edit_config()
        return

    if list_hidden:
        list_hidden_commands(full_output=full_output, only_exports=only_exports)
        return

    if ids_to_hide:
        hide_commands(ids_to_hide)

    if ids_to_unhide:
        unhide_commands(ids_to_unhide)

    # If we are working with categories, run those commands
    if category or uncategorized:
        category_display(
            input_string=UNKNOWN_CATEGORY_NAME if uncategorized else input_string,
            list_categories=show_list,
            full_output=full_output,
            only_exports=only_exports,
        )

    # If we are working with commands, run those commands
    if show_list:
        command_list(full_output=full_output, only_exports=only_exports)

    if input_string:
        command_display(input_string, full_output=full_output)

    if not input_string:
        typer.echo(typer.style("No command specified", fg="red", bold=True))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
