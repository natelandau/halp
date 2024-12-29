"""Edit command descriptions."""

import typer
from loguru import logger
from rich.prompt import Prompt

from halper.models import Command
from halper.utils import console


def edit_command_description(command_id: int) -> None:
    """Update a command's description by prompting user for new text.

    Interactively prompt user to edit a command's description by displaying the current description
    and allowing them to input a new one. This allows customizing command documentation to be more
    relevant or clearer. The function handles all user interaction, database updates, and error cases.

    Args:
        command_id: int - ID of the command to edit. If not found, will exit with error.

    Raises:
        typer.Exit: If command ID not found or on successful completion.
        typer.Abort: If user declines confirmation prompt.

    Example:
        edit_command_description(5)  # Will prompt user to edit description of command with ID 5
    """
    command = Command.get_or_none(Command.id == command_id)
    if not command:
        logger.error(f"No command found with ID {command_id}")
        raise typer.Exit(code=1)

    console.print(f"Editing description for command [code]{command.name}[/code]")
    console.print(f"Current description: [code]{command.escaped_desc}[/code]")
    console.rule()
    new_description = Prompt.ask("New description")

    new_description_display = new_description.replace("[", "\\[")
    confirm = Prompt.ask(
        f"Set description to [code]{new_description_display}[/code]?", choices=["y", "n"]
    )
    if confirm.lower() == "n":
        raise typer.Abort()

    command.description = new_description
    command.has_custom_description = True
    command.save()

    logger.info(f"Updated description for command {command.name}")
    console.print(f"Updated description for command [bold]{command.name}[/bold]")

    raise typer.Exit(code=0)
