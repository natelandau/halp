"""Views for list subcommand."""

import inflect
from rich import box
from rich.columns import Columns
from rich.table import Table

from halper.constants import CommandType
from halper.models import Command

p = inflect.engine()


def column_view(
    strings: list[str],
    name: str,
    *,
    equal_width: bool = True,
) -> Columns:
    """Create a formatted column view for displaying strings in a terminal.

    Create a Rich Columns object that displays a list of strings in a formatted column layout with an auto-generated title showing the count. Useful for presenting lists of items in an organized, space-efficient way with consistent column widths.

    Args:
        strings (list[str]): List of strings to display in columns
        name (str): Singular form of the item name, used to generate plural title
        equal_width (bool, optional): Force all columns to have equal width. Defaults to True.

    Returns:
        Columns: Rich Columns object configured with the provided strings and formatting
    """
    return Columns(
        strings,
        equal=equal_width,
        expand=True,
        title=f"[bold underline]{len(strings)} {p.plural_noun(name, len(strings))}[/bold underline]",
    )


def command_table_view(
    commands: list[Command],
    title: str = "",
    *,
    show_categories: bool = False,
    show_hidden: bool = False,
    full_output: bool = False,
) -> Table:
    """Create a rich table displaying command information.

    Create a formatted table showing command details like name, categories, type and description. Useful for presenting command data in a clear, organized way with configurable display options.

    Args:
        commands (list[Command]): List of Command objects to display
        title (str, optional): Title text for the table. Defaults to "".
        show_categories (bool, optional): Show category column. Defaults to False.
        show_hidden (bool, optional): Show hidden commands. Defaults to False.
        full_output (bool, optional): Show all available columns. Defaults to False.

    Returns:
        Table: Rich Table object containing formatted command data, or None if no commands to display

    The table adapts its columns based on the display options:
    - Basic view shows command name and description
    - Categories view adds category column
    - Full view shows all columns including type, ID and file path
    """
    commands_to_display = [c for c in commands if c.hidden == show_hidden]
    if not commands_to_display:
        return None

    table = Table(
        box=box.HORIZONTALS,
        expand=False,
        show_header=True,
        title=title or None,
        caption=f"{len(commands_to_display)} {p.plural_noun('command', len(commands_to_display))}",
        caption_justify="right",
    )
    columns = [
        ("Command", "bold", True),
        ("Category", "dim", show_categories),
        ("Description", "", True),
        ("Type", "dim", full_output),
        ("ID", "dim cyan", full_output or show_hidden),
        ("File", "dim", full_output),
    ]

    for column in columns:
        name, style, display = column
        if display:
            table.add_column(name, style=style)

    for c in commands_to_display:
        description = (
            c.escaped_desc
            if c.description
            else c.code_syntax()
            if c.command_type in {CommandType.ALIAS.name, CommandType.EXPORT.name}
            else ""
        )
        row_values = [
            c.name,
            ", ".join(c.category_names),
            description,
            c.command_type.title() if full_output else "",
            str(c.id) if full_output or show_hidden else "",
            c.file.name if full_output else "",
        ]

        table.add_row(
            *[value for value, (_, _, display) in zip(row_values, columns, strict=False) if display]
        )

    return table
