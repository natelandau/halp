"""List subcommand."""

import cappa
from rich.table import Table

from halper.controllers import fetch_categories, fetch_commands_from_category
from halper.halp import Halp, ListCommand
from halper.models import Command
from halper.utils import console, pp
from halper.views import column_view, command_table_view

from .helpers import initialize_subcommand


def list_command(halp: Halp, cmd: ListCommand) -> None:
    """Display filtered command information in a formatted table view.

    List and display commands from the database in a tabular format, with options to filter by category and control the output format. This function serves as the main handler for the 'list' subcommand, allowing users to browse available commands and categories in an organized way.

    Args:
        halp (Halp): Application configuration and settings object.
        cmd (ListCommand): Command line arguments and flags for the list subcommand.

    Raises:
        cappa.Exit: Exit with code 1 if there's a database error, or code 0 for normal completion
            after displaying categories.

    The function supports two main modes:
        1. Category-based listing: Filter and display commands by category, or show category statistics
        2. Full listing: Display all commands in a single table with configurable detail levels
    """  # noqa: DOC502
    initialize_subcommand(halp=halp, subcommand=cmd, require_db_content=True)
    if cmd.category or cmd.list_categories:
        categories = fetch_categories(cmd.category)

        if not categories:
            pp.error(f"No category found matching: '{cmd.category}'")
            raise cappa.Exit(code=1)

        if cmd.list_categories:
            console.print("")
            table = Table.grid(expand=False, padding=(0, 5))
            table.add_column()
            table.add_column()
            table.add_row("Category", "# Commands", style="bold underline")
            for category in categories:
                commands = fetch_commands_from_category(category, show_hidden=cmd.show_hidden)
                count = len(commands)
                table.add_row(category.name, f"{count}")
            console.print(table)
            raise cappa.Exit(code=0)

        for category in categories:
            cat_commands = fetch_commands_from_category(category, show_hidden=cmd.show_hidden)
            if cmd.short:
                columns = column_view([x.name for x in cat_commands], f"{category.name} command")
                console.print(columns)
                console.print("")
                continue

            table = command_table_view(
                commands=cat_commands,
                full_output=cmd.full,
                show_categories=False,
                title=f"[bold underline]{category.name}[/bold underline]\n{category.description}"
                if category.description
                else category.name,
            )
            console.print(table)

        raise cappa.Exit(code=0)

    results = Command.select().where(Command.hidden == cmd.show_hidden).order_by(Command.name)

    if not results:
        pp.info("No commands found")
        raise cappa.Exit(code=1)

    if cmd.short:
        columns = column_view([x.name for x in results], "command")
        console.print(columns)
        raise cappa.Exit(code=0)

    table = command_table_view(
        commands=results,
        full_output=cmd.full,
        show_categories=True,
        show_hidden=cmd.show_hidden,
    )
    console.print(table)
    raise cappa.Exit(code=0)
