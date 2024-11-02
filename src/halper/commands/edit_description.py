"""Edit command descriptions."""

import typer
from loguru import logger
from rich.prompt import Prompt

from halper.models import Command
from halper.utils import console


def edit_command_description(command_id: int) -> None:
    """Edit command description by ID."""
    command = Command.get_or_none(Command.id == command_id)
    if not command:
        logger.error(f"No command found with ID {command_id}")
        raise typer.Exit(code=1)  # noqa: DOC501

    console.print(f"Editing description for command [code]{command.name}[/code]")
    console.print(f"Current description: [code]{command.escaped_desc}[/code]")
    console.rule()
    new_description = Prompt.ask("New description")

    new_description_display = new_description.replace("[", "\\[")
    confirm = Prompt.ask(
        f"Set description to [code]{new_description_display}[/code]?", choices=["y", "n"]
    )
    if confirm.lower() == "n":
        raise typer.Abort()  # noqa: DOC501

    command.description = new_description
    command.has_custom_description = True
    command.save()

    logger.info(f"Updated description for command {command.name}")
    console.print(f"Updated description for command [bold]{command.name}[/bold]")

    raise typer.Exit(code=0)
