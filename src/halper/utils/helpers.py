"""Helper functions for the halp package."""

import sys

import sh
from rich import box
from rich.table import Table

from halper.constants import CommandType
from halper.models.database import Category, Command, CommandCategory


def list_commands(  # noqa: PLR0917
    category: Category | None = None,
    commands: list[Command] | None = None,
    show_hidden: bool = False,
    show_categories: bool = False,
    full_output: bool = False,
    only_exports: bool = False,
    title: str | None = None,
) -> Table:
    """List commands in a table.

    Args:
        category (Category): A Category object.
        commands (list[Command]): A list of Command objects.
        show_categories (bool): Whether to show categories.
        show_hidden (bool): Whether to show hidden commands.
        full_output (bool): Whether to show full output.
        only_exports (bool): Whether to show only export commands.
        title (str): A title for the table.

    Returns:
        Table | None: A 'rich' Table object containing the formatted command data. Returns None if the table has no rows (i.e., there are no commands to display).
    """
    if category:
        commands_to_display = (
            Command.select()
            .where(Command.hidden == show_hidden)
            .join(CommandCategory)
            .join(Category)
            .where(Category.id == category.id)
            .order_by(Command.name)
        )
        table_title = (
            f"[bold]{category.name}[/bold]\n{category.description}"
            if category.description
            else category.name
        )

    elif commands:
        commands_to_display = [c for c in commands if c.hidden == show_hidden]
        table_title = title

    table = Table(
        box=box.SIMPLE,
        expand=False,
        show_header=True,
        title=table_title,
    )

    columns = (
        {"name": "Command", "style": "bold", "display": True},
        {"name": "Categories", "style": "dim", "display": show_categories},
        {"name": "Type", "style": "dim", "display": full_output},
        {"name": "Description", "style": "dim", "display": True},
        {"name": "ID", "style": "dim cyan", "display": full_output or show_hidden},
        {"name": "File", "style": "dim", "display": full_output},
    )

    for column in columns:
        if column["display"]:
            table.add_column(str(column["name"]), style=str(column["style"]))

    for c in commands_to_display:
        if only_exports and c.command_type != CommandType.EXPORT.name:
            continue

        if not only_exports and not full_output and c.command_type == CommandType.EXPORT.name:
            continue

        command_categories = (
            Category().select().join(CommandCategory).join(Command).where(Command.id == c.id)
        )

        description = (
            c.description
            if c.description
            else c.code_syntax()
            if c.command_type in {CommandType.ALIAS.name, CommandType.EXPORT.name}
            else ""
        )

        column_data = (
            {"value": c.name, "display": True},
            {
                "value": ", ".join([category.name for category in command_categories]),
                "display": show_categories,
            },
            {"value": c.command_type.title(), "display": full_output},
            {"value": description, "display": True},
            {"value": str(c.id), "display": full_output or show_hidden},
            {"value": c.file.name, "display": full_output},
        )

        table.add_row(*[column["value"] for column in column_data if column["display"]])

    return table if table.rows else None


def get_tldr_command() -> sh.Command | None:
    """Get the 'tldr' command if available.

    Returns:
        An instance of sh.Command configured for 'tldr' if available,
        otherwise None.
    """
    try:
        tldr_path = sh.which("tldr").strip()
        return sh.Command(tldr_path).bake("-q")
    except sh.ErrorReturnCode:
        return None


def check_python_version() -> bool:
    """Check the Python version.

    Returns:
        bool: True if the Python version is >= 3.9, False otherwise.
    """
    return sys.version_info >= (3, 10)
