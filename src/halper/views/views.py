"""Views for the halper app."""

import inflect
from rich import box
from rich.columns import Columns
from rich.table import Table

from halper.constants import CommandType
from halper.models.database import Category, Command, CommandCategory
from halper.utils import console

p = inflect.engine()


def strings_to_columns(name: str, strings: list[str], equal: bool = True) -> Columns:
    """Convert a list of strings to a rich Columns object."""
    return Columns(
        strings,
        equal=equal,
        expand=True,
        title=f"[bold underline]{len(strings)} {p.plural_noun(name, len(strings))}[/bold underline]",
    )


def display_commands(
    commands: list[Command], input_string: str, full_output: bool, found_in_tldr: bool
) -> None:
    """Display detailed information for a set of commands.

    Args:
        commands: The commands to display.
        input_string: The input string used to search for the commands.
        full_output: Whether to display full command information.
        found_in_tldr: Whether the command was found in tldr.
    """
    show_id = len(commands) > 1

    if show_id:
        console.print(
            f"[bold]Found {len(commands)} commands matching:[/bold] [code]{input_string}[/code]"
        )

    for command in commands:
        if show_id:
            console.rule()

        console.print(
            command.table(
                full_output=full_output, found_in_tldr=found_in_tldr, show_id=full_output or show_id
            )
        )

    if show_id:
        console.rule()


def command_list_table(  # noqa: PLR0917
    category: Category | None = None,
    commands: list[Command] | None = None,
    show_hidden: bool = False,
    show_categories: bool = False,
    full_output: bool = False,
    only_exports: bool = False,
    title: str | None = None,
) -> Table | None:
    """List commands in a table, filtered and formatted based on the provided parameters.

    Args:
        category (Optional[Category]): A Category object to filter commands.
        commands (Optional[list[Command]]): A list of Command objects to display.
        show_hidden (bool): Whether to show hidden commands.
        show_categories (bool): Whether to show categories.
        full_output (bool): Whether to show full output.
        only_exports (bool): Whether to show only export commands.
        title (Optional[str]): A title for the table.

    Returns:
        Optional[Table]: A 'rich' Table object containing the formatted command data, or None if no commands to display.
    """
    commands_to_display = []

    if category:
        # Filter commands by category
        commands_to_display = (
            Command.select()
            .where(Command.hidden == show_hidden)
            .join(CommandCategory)
            .join(Category)
            .where(Category.id == category.id)
            .order_by(Command.name)
        )

    elif commands:
        # Use provided command list
        commands_to_display = [c for c in commands if c.hidden == show_hidden]

    if not commands_to_display:
        return None

    table = Table(
        box=box.SIMPLE,
        expand=False,
        show_header=True,
        title=title,
        caption=f"{len(commands_to_display)} commands",
        caption_justify="right",
    )
    columns = [
        ("Command", "bold", True),
        ("Categories", "dim", show_categories),
        ("Type", "dim", full_output),
        ("Description", "dim", True),
        ("ID", "dim cyan", full_output or show_hidden),
        ("File", "dim", full_output),
    ]

    # Add columns based on display condition
    for name, style, display in columns:
        if display:
            table.add_column(name, style=style)

    for c in commands_to_display:
        if only_exports and c.command_type != CommandType.EXPORT.name:
            continue
        if not only_exports and not full_output and c.command_type == CommandType.EXPORT.name:
            continue

        description = (
            c.description
            if c.description
            else c.code_syntax()
            if c.command_type in {CommandType.ALIAS.name, CommandType.EXPORT.name}
            else ""
        )
        row_values = [
            c.name,
            ", ".join(c.category_names),
            c.command_type.title() if full_output else "",
            description,
            str(c.id) if full_output or show_hidden else "",
            c.file.name if full_output else "",
        ]

        # Add row to table
        table.add_row(
            *[value for value, (_, _, display) in zip(row_values, columns, strict=False) if display]
        )

    return table
