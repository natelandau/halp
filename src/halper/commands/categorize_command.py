"""Categorize command by ID."""

import typer
from loguru import logger
from rich.prompt import Prompt

from halper.models import Category, Command, CommandCategory
from halper.utils import console


def categorize_command(command_id: int | None = None) -> None:
    """Categorize command by ID."""
    command = Command.get_or_none(Command.id == command_id)
    if not command:
        logger.error(f"Command with ID {command_id} not found")
        raise typer.Exit(code=1)

    categories = Category.select()

    console.print("[bold underline]Select a category to categorize the command:[/bold underline]")
    for category in categories:
        console.print(f"  {category.id:>2}: {category.name}")

    console.print("[cyan]   A: Abort")

    choices = [str(category.id) for category in categories]
    choices.extend(["A", "a"])
    new_category_id = Prompt.ask(
        "\nCategory ID",
        choices=choices,
        show_choices=False,
        console=console,
        default="A",
        show_default=False,
    )

    if new_category_id.upper() == "A":
        console.print("\nAborting categorization")
        raise typer.Exit()

    new_category_obj = Category.get(int(new_category_id))

    confirm = Prompt.ask(
        f"Categorize [bold]{command.name}[/bold] to [code]{new_category_obj.name}[/code]?",
        choices=["y", "n"],
    )
    if confirm.lower() == "n":
        raise typer.Abort()

    all_command_categories = CommandCategory.select().where(CommandCategory.command == command)
    for command_category in all_command_categories:
        command_category.delete_instance()

    CommandCategory.create(command=command, category=new_category_obj, is_custom=True)

    console.print(
        f"\nCommand [bold]{command.name}[/bold] has been categorized to [code]{new_category_obj.name}[/code]"
    )
    raise typer.Exit()
