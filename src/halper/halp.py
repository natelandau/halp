"""The halp cli."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa
from rich.console import Console

from halper.constants import DB_PATH, PrintLevel
from halper.utils import pp, validate_settings

console = Console()


@dataclass
class Halp:
    """Halp - Your one stop shop for command line help.

    Halp rolls three different services into one simple CLI tool:

    - Finds and indexes your **custom shell functions and aliases**
    - Uses **comments within your dotfiles to provide descriptions** for each command
    - Adds your commands into **customizable and searchable categories**
    - **Search for your commands using regex** against their name, description, or code
    - **Access simplified man pages for builtin commands** with [TLDR pages](https://tldr.sh/)
    - **Explain builtin commands with options or pipes** from [mankier.com](https://www.mankier.com/explain)

    Read the help for each subcommand for more information.
    """

    command: cappa.Subcommands[
        IndexCommand | ListCommand | HideCommand | SearchCommand | ConfigCommand | UnhideCommand
    ]

    verbosity: Annotated[
        PrintLevel,
        cappa.Arg(
            short=True,
            count=True,
            help="Verbosity level (`-v` or `-vv`)",
            choices=[],
            show_default=False,
            propagate=True,
        ),
    ] = PrintLevel.INFO


@cappa.command(
    name="hide",
    invoke="halper.cli.hide.hide_command",
    help="Hide subcommand by ID",
    description="""
This command is helpful to hide commands that you don't want to see in the list of commands. Some commone use cases are:
- Multiple commands with the same name within your dotfiles
- Private functions or aliases

You can get the ID of a command by running `halp list --full`

You can hide multiple commands by passing a comma separated list of IDs.
    """,
)
class HideCommand:
    """Hide subcommand."""

    commands: Annotated[
        list[str],
        cappa.Arg(help="List of command IDs to hide", value_name="Command IDS"),
    ]


@cappa.command(
    name="unhide",
    invoke="halper.cli.unhide.unhide_command",
    help="Unhide subcommand by ID",
    description="You can get the ID of a command by running `halp list --full`",
)
class UnhideCommand:
    """Unhide subcommand."""

    commands: Annotated[
        list[str],
        cappa.Arg(help="List of command IDs to unhide", value_name="Command IDS"),
    ]


@cappa.command(
    name="index",
    invoke="halper.cli.index.index_command",
    help="Create a searchable database of your commands",
    description=f"This will create a SQLite database at `{DB_PATH}`",
)
class IndexCommand:
    """Index subcommand."""

    rebuild: Annotated[
        bool,
        cappa.Arg(
            help="Rebuild the index from scratch removing all customizations",
            short=True,
        ),
    ] = False


@cappa.command(name="list", invoke="halper.cli.list.list_command", help="View indexed commands")
class ListCommand:
    """List subcommand."""

    category: Annotated[
        str,
        cappa.Arg(
            help="Filter commands by category containing the given string.",
        ),
    ] = ""
    list_categories: Annotated[
        bool,
        cappa.Arg(
            long="list-categories/cats",
            help="List all categories.",
            show_default=False,
        ),
    ] = False

    short: Annotated[
        bool,
        cappa.Arg(
            short=True,
            help="Display condensed command information.",
        ),
    ] = False

    full: Annotated[
        bool,
        cappa.Arg(
            short=True,
            help="Display detailed command information.",
        ),
    ] = False
    show_hidden: Annotated[
        bool,
        cappa.Arg(
            help="Show hidden commands.",
            long="--hidden",
            short="x",
        ),
    ] = False


@cappa.command(
    name="search", invoke="halper.cli.search.search_command", help="Search indexed commands"
)
class SearchCommand:
    """Search subcommand."""

    input_string: Annotated[
        str | None,
        cappa.Arg(
            help="""Command name to search for.\\
If paired with `--regex`, the search string will be used as a regex pattern.""",
            value_name="Search string",
        ),
    ] = None

    show_hidden: Annotated[
        bool,
        cappa.Arg(
            help="Show hidden commands.",
            long="--hidden",
            short="x",
        ),
    ] = False

    regex: Annotated[
        bool,
        cappa.Arg(
            short=True,
            help="Use **case insensitive regex** to search for the command.",
        ),
    ] = False

    search_code: Annotated[
        bool,
        cappa.Arg(
            short="-c",
            help="Search within the code of the command using regex.",
        ),
    ] = False


@cappa.command(
    name="config",
    invoke="halper.cli.config.config_command",
    help="Create a configuration file",
    description="""\
Creates a configuration file at `~/.config/halp/config.toml` if it doesn't exist populated with default values.

Optionally, you can run the command with `--interactive` to modify the default values.
               """,
)
class ConfigCommand:
    """Config subcommand."""

    interactive: Annotated[
        bool,
        cappa.Arg(
            short=True,
            help="Create configuration file interactively.",
        ),
    ] = False


def main() -> None:  # pragma: no cover
    """Main function."""
    try:
        cappa.invoke(obj=Halp, deps=[validate_settings])
    except KeyboardInterrupt as e:
        pp.info("Exiting...")
        raise cappa.Exit(code=1) from e


if __name__ == "__main__":  # pragma: no cover
    main()
