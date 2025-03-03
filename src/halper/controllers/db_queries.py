"""Database queries."""

import cappa
from peewee import PeeweeException

from halper.models import Category, Command, CommandCategory
from halper.utils import pp


def fetch_categories(search_string: str) -> list[Category]:
    """Fetch and filter categories from the database based on a search string.

    Query the database for categories whose names contain the given search string. This function is useful when implementing category-based filtering or search functionality in the application. Results are ordered alphabetically by category name.

    Args:
        search_string (str): String to filter category names by. Categories whose names contain this string will be returned.

    Returns:
        list[Category]: List of matching Category objects ordered by name.

    Raises:
        cappa.Exit: Exit with code 1 if there's a database error during the query.
    """
    try:
        return (
            Category.select()
            .where(Category.name.contains(search_string))
            .order_by(Category.name)
            .execute()
        )
    except PeeweeException as e:
        pp.error(f"Error fetching categories: {e}")
        raise cappa.Exit(code=1) from e


def fetch_commands_from_category(category: Category, *, show_hidden: bool = False) -> list[Command]:
    """Fetch and filter commands belonging to a specific category.

    Query the database for commands associated with the given category, with optional filtering for hidden commands. Results are ordered alphabetically by command name. This function enables category-based command organization and filtering in the application's UI.

    Args:
        category (Category): Category object to fetch commands for
        show_hidden (bool, optional): Whether to include hidden commands in results. Defaults to False.

    Returns:
        list[Command]: List of Command objects belonging to the category, ordered by name.

    Raises:
        cappa.Exit: Exit with code 1 if there's a database error during the query.
    """
    try:
        return (
            Command.select()
            .where(Command.hidden == show_hidden)
            .join(CommandCategory)
            .join(Category)
            .where(Category.id == category.id)
            .order_by(Command.name)
            .execute()
        )
    except PeeweeException as e:
        pp.error(f"Error fetching commands from category: {e}")
        raise cappa.Exit(code=1) from e
