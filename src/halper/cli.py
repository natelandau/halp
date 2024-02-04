"""Halp CLI."""

from pathlib import Path
from typing import Annotated, Optional

import peewee
import typer
from loguru import logger

from halper.__version__ import __version__

# isort:skip
from halper.commands import (
    categorize_command,
    category_display,
    command_display,
    command_list,
    edit_command_description,
    hide_commands,
    list_hidden_commands,
    search_commands,
    unhide_commands,
)
from halper.config import HalpConfig
from halper.constants import APP_DIR, DB, SearchType
from halper.models import Database, Indexer
from halper.utils import (
    check_python_version,
    console,
    edit_config,
    instantiate_logger,
    validate_config,
)

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
    categorize: Annotated[
        Optional[int],
        typer.Option("--categorize", help="Categorize command by ID", show_default=False),
    ] = None,
    edit_description_id: Annotated[
        Optional[int],
        typer.Option(
            "--description", help="Customize command description by ID", show_default=False
        ),
    ] = None,
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
    search_code: Annotated[
        Optional[str],
        typer.Option(
            "--search-code", help="Search for command code matching this regex", show_default=False
        ),
    ] = None,
    search_name: Annotated[
        Optional[str],
        typer.Option(
            "--search-name", help="Search command names matching this regex", show_default=False
        ),
    ] = None,
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
    # MAINTENANCE COMMANDS ######################
    edit_configuration: Annotated[
        bool,
        typer.Option(
            "--edit-config",
            help="Edit the configuration file",
            show_default=True,
            rich_help_panel="Maintenance Commands",
        ),
    ] = False,
    index: Annotated[
        bool,
        typer.Option(
            "--index",
            help="Index files for changes. [dim](Maintain customizations)[/dim]",
            rich_help_panel="Maintenance Commands",
        ),
    ] = False,
    index_full: Annotated[
        bool,
        typer.Option(
            "--index-full",
            help="Completely rebuild index of commands. [dim](Remove customizations)[/dim]",
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
    Point Halp at the appropriate dotfiles and it will index all your custom aliases and functions and add them to categories you specify. Then you can query it to find your commands and their usage.

    [bold]Before you can use Halp, you must first[/bold]

        1. Create a configuration file by running 'halp --edit-config'.
        2. Index your commands. You can do this by running 'halp --index'.

    [bold]Usage Examples:[/bold]

    [dim]Search for a command by name[/dim]
    halp <command name>

    [dim]See full output of a command[/dim]
    halp --full  <command>

    [dim]View all commands in a particular category[/dim]
    halp --category <category>

    [dim]Edit the configuration file[/dim]
    halp --edit-config

    [dim]Hide commands that you don't want to see[/dim]
    halp --hide <command ID>,<command ID>,...

    [dim]Customize the description of a command[/dim]
    halp --description <command ID>

    [dim]Search for commands who's code matches a regex pattern[/dim]
    halp --search-code <regex pattern>

    """  # noqa: D301
    # Instantiate Logging
    instantiate_logger(verbosity, log_file, log_to_file)

    if not check_python_version():
        logger.error("Python version must be >= 3.10")
        raise typer.Exit(code=1)

    if edit_configuration:
        edit_config()
        raise typer.Exit(0)

    validate_config()

    # Instantiate Database
    try:
        db = Database(DB)
        db.instantiate(current_version=__version__)
    except peewee.OperationalError as e:
        logger.exception(f"Unable to instantiate database: {e}")
        raise typer.Exit(code=1) from e

    if db.is_empty() and (not index and not index_full):
        console.print(
            "No commands found.\nMake sure your configuration file is up to date and run [code]halp --index[/code] to index your commands."
        )
        raise typer.Exit(code=1)

    # Process options
    if index or index_full:
        indexer = Indexer(rebuild=index_full)
        indexer.do_index()
        raise typer.Exit(0)

    if list_hidden:
        list_hidden_commands(full_output=full_output, only_exports=only_exports)
        raise typer.Exit(0)

    if ids_to_hide:
        hide_commands(ids_to_hide)

    if ids_to_unhide:
        unhide_commands(ids_to_unhide)

    if edit_description_id:
        edit_command_description(edit_description_id)

    if categorize:
        categorize_command(categorize)

    if search_code or search_name:
        # TODO: Testing this function is difficult because of the custom regex function not working in the mocked database
        search_type, pattern = (
            (SearchType.CODE, search_code) if search_code else (SearchType.NAME, search_name)
        )
        search_commands(search_type=search_type, pattern=pattern, full_output=full_output)

    # If we are working with categories, run those commands
    if category or uncategorized:
        category_display(
            input_string=HalpConfig().uncategorized_name if uncategorized else input_string,
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
