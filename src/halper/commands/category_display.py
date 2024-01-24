"""Category display functionality of Halp."""

import peewee
import typer
from loguru import logger

from halper.models import Category
from halper.utils import console
from halper.views import command_list_table, strings_to_columns


def category_display(
    input_string: str | None = None,
    list_categories: bool = False,
    full_output: bool = False,
    only_exports: bool = False,
) -> None:
    """Display categories based on the input criteria.

    Args:
        input_string: A string to filter the categories, None for no filtering.
        list_categories: Boolean indicating whether to list all categories.
        full_output: Boolean indicating if full output should be displayed.
        only_exports: Boolean indicating if only exports should be displayed.

    Raises:
        typer.Exit: Exits the application with a status code. The status code is 1 if either no categories are found, and 0 upon successful completion.
    """
    try:
        query = Category.select()
        if input_string:
            query = query.where(Category.name.contains(input_string))
        categories = query.order_by(Category.name).execute()
    except peewee.PeeweeException as e:
        logger.exception(f"Error fetching categories: {e}")
        raise typer.Exit(code=1) from e

    if not list(categories):
        if input_string:
            console.print(f"No categories found matching: [bold]{input_string}[/bold]")
        else:
            console.print("No categories found.")

        raise typer.Exit(code=1)

    if list_categories:
        category_names = [category.name for category in categories]
        columns = strings_to_columns(name="category", strings=category_names)
        console.print(columns)

        raise typer.Exit()

    for category in categories:
        table = command_list_table(
            category=category,
            full_output=full_output,
            only_exports=only_exports,
            title=f"[bold underline]{category.name}[/bold underline]\n{category.description}"
            if category.description
            else category.name,
        )
        if table:
            console.print(table)

    raise typer.Exit()
