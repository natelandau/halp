"""Database models for the HALP app."""
import os
import re

from loguru import logger
from peewee import BooleanField, ForeignKeyField, Model, PeeweeException, SqliteDatabase, TextField
from rich.syntax import Syntax
from rich.table import Table
from semver.version import Version

from halper.config import HalpConfig
from halper.constants import APP_DIR, DB, DB_PATH, CommandType
from halper.utils import errors


class BaseModel(Model):
    """Base model for HALP models."""

    class Meta:
        """Meta class for base model."""

        database = DB


class HalpInfo(BaseModel):
    """HALP info model."""

    version = TextField()


class File(BaseModel):
    """Files model."""

    name = TextField()
    path = TextField()


class TempFile(BaseModel):
    """Temporary files model."""

    name = TextField()
    path = TextField()


class Category(BaseModel):
    """Categories model."""

    name = TextField(unique=True)
    description = TextField(null=True)
    code_regex = TextField(null=True)
    comment_regex = TextField(null=True)
    command_name_regex = TextField(null=True)
    path_regex = TextField(null=True)


class TempCategory(BaseModel):
    """Temporary categories model."""

    name = TextField(unique=True)
    description = TextField(null=True)
    code_regex = TextField(null=True)
    comment_regex = TextField(null=True)
    command_name_regex = TextField(null=True)
    path_regex = TextField(null=True)


class Command(BaseModel):
    """Commands model."""

    code = TextField()
    command_type = TextField()  # CommandType enum value
    description = TextField(null=True)
    file = ForeignKeyField(File, backref="commands", null=True)
    name = TextField(index=True)
    hidden = BooleanField(default=False)
    has_custom_description = BooleanField(default=False)

    def __str__(self) -> str:
        """Return string representation of command."""
        return (
            f"{self.name=}\n{self.description=}\n{self.command_type=}\n{self.code=}\n{self.file=}\n"
        )

    @property
    def category_names(self) -> list[str]:
        """Return a list of category names associated with this command.

        Retrieves the names of categories linked to the current command instance
        from the database, ordered alphabetically by category name.

        Returns:
            list[str]: A list of category names.
        """
        # Retrieve category names associated with this command
        category_query = (
            Category.select(Category.name)
            .join(CommandCategory)
            .join(Command)
            .where(Command.id == self.id)
            .order_by(Category.name)
        )

        # Construct the list of category names
        return [category.name for category in category_query]

    def table(
        self, full_output: bool = False, found_in_tldr: bool = False, show_id: bool = False
    ) -> Table:
        """Return rich table for command.

        Args:
            full_output (bool, optional): Whether to display full output. Defaults to False.
            found_in_tldr (bool, optional): Whether command was found in `tldr`. Defaults to False.
            show_id (bool, optional): Whether to display command ID. Defaults to False.

        Returns:
            rich.Table: Rich table for command
        """
        grid = Table.grid(expand=False, padding=(0, 1))
        grid.add_column(style="bold")
        grid.add_column()
        grid.add_row("Command:", f"[bold]{self.name}[/bold]")
        if show_id:
            grid.add_row("ID:", f"[cyan]{self.id!s}[/cyan]")
        grid.add_row("Description:", self.description)
        grid.add_row("Categories:", ", ".join(self.category_names))
        grid.add_row("Type:", self.command_type.title())
        grid.add_row("File:", f"[dim]{self.file.path}[/dim]")
        if found_in_tldr:
            grid.add_row("TLDR:", f"View TLDR entry with [code]tldr {self.name}[/code]")
        if full_output:
            grid.add_row("Code:", self.code_syntax(padding=True))
        return grid

    def code_syntax(self, padding: bool = False) -> Syntax:
        """Return rich syntax for command code."""
        pad = (1, 2) if padding else (0, 0)

        match self.command_type:
            case CommandType.ALIAS.name:
                return Syntax(self.code, "shell", dedent=True, padding=pad)
            case CommandType.EXPORT.name:
                return Syntax(f"{self.name}={self.code}", "shell", dedent=True, padding=pad)
            case CommandType.FUNCTION.name:
                # Remove leading newline if present
                code = self.code.splitlines()
                if code and not code[0] and len(code) > 1:
                    code = code[1:]
                return Syntax("\n".join(code), "shell", dedent=True, padding=pad)
            case _:
                return Syntax(self.code, "shell")


class TempCommand(BaseModel):
    """Temporary commands model."""

    code = TextField()
    command_type = TextField()
    description = TextField(null=True)
    file = ForeignKeyField(TempFile, backref="commands", null=True)
    name = TextField(index=True)
    hidden = BooleanField(default=False)
    has_custom_description = BooleanField(default=False)


class CommandCategory(BaseModel):
    """Command categories model."""

    command = ForeignKeyField(Command, backref="categories")
    category = ForeignKeyField(Category, backref="commands")
    is_custom = BooleanField(default=False)

    def __str__(self) -> str:
        """Return string representation of command category."""
        return f"{self.command=}, {self.category=}, {self.is_custom=}"


class TempCommandCategory(BaseModel):
    """Temporary command categories model."""

    command = ForeignKeyField(TempCommand, backref="categories")
    category = ForeignKeyField(TempCategory, backref="commands")
    is_custom = BooleanField(default=False)


# Custom regexp function for SQLite. Registered in Database.instantiate()
def regexp(pattern: str, value: str) -> bool:
    """Evaluate a regular expression pattern against a given string value.

    Args:
        pattern (str): The regular expression pattern to search for.
        value (str): The string value to be searched.

    Returns:
        bool: True if the pattern is found in the value, False otherwise.
    """
    case_sensitive_regex = 0 if HalpConfig().case_sensitive else re.IGNORECASE
    return re.search(pattern, value, flags=case_sensitive_regex) is not None


class Database:
    """Database controller for the HALP app."""

    def __init__(self, database: SqliteDatabase = DB) -> None:
        """Initialize database."""
        self.db = database

    def instantiate(self, current_version: str) -> None:
        """Instantiate database."""
        logger.trace(f"Instantiating database. {APP_DIR=} {DB_PATH=}")

        # Check if the directory exists
        if not DB_PATH.parent.exists():
            msg = f"Directory does not exist: {DB_PATH.parent}"
            raise errors.AppDirectoryError(msg)

        # Check file permissions
        if not os.access(DB_PATH.parent, os.W_OK):
            msg = f"Write permission is not available on {DB_PATH.parent}"
            raise errors.AppDirectoryError(msg)

        self.db.connect()
        self.db.create_tables(
            [
                Category,
                Command,
                CommandCategory,
                File,
                HalpInfo,
            ]
        )

        # Register the regexp function with the SQLite database
        DB.register_function(regexp, "REGEXP")

        # Migrate the db if necessary
        self.migrate_db(current_version)

        # Add current version to the database
        try:
            halp_info, created = HalpInfo.get_or_create(id=1, defaults={"version": current_version})
            if not created:
                halp_info.version = current_version
                halp_info.save()
        except PeeweeException as e:
            logger.error(f"Failed to add current version to the database: {e}")
            raise

    def close(self) -> None:
        """Close database."""
        self.db.close()

    def is_empty(self) -> bool:
        """Check if database has no commands."""
        return not self.has_data([Command])

    def migrate_db(self, current: str) -> None:
        """Migrate the database from old to new versions."""
        current_version = Version.parse(current)
        halp_info = HalpInfo.get_or_none(1)
        if not halp_info:
            return

        db_version = Version.parse(halp_info.version)
        if db_version == current_version:
            return

        from playhouse.migrate import SqliteMigrator, migrate  # noqa: PLC0415

        migrator = SqliteMigrator(self.db)

        if db_version <= Version.parse("0.3.0") and current_version > Version.parse("0.3.0"):
            # Add 'is_instance' column to CommandCategory
            logger.debug(f"Upgrade database from {db_version} to {current_version}")
            with self.db.atomic():
                migrate(
                    migrator.add_column("commandcategory", "is_custom", BooleanField(default=False))
                )

    @staticmethod
    def clear_data(tables: list[Model]) -> None:
        """Clear all data from the specified Peewee ORM tables.

        Deletes all records from each table in the provided list. Logs the result of
        each deletion attempt.

        Args:
            tables (List[Model]): A list of Peewee table classes to be cleared.

        Raises:
            PeeweeException: If a Peewee-specific error occurs during deletion.
            DatabaseError: If a database error occurs during deletion.
        """
        try:
            for table in tables:
                delete_count = table.delete().execute()
                logger.debug(f"Cleared {delete_count} records from {table.__name__}.")
        except PeeweeException as e:
            logger.error(f"Failed to clear data from {table.__name__}: {e}")
            raise

    @staticmethod
    def has_data(tables: list[Model]) -> bool:
        """Check whether any of the specified Peewee ORM tables contain data.

        Args:
            tables (list[Model]): A list of Peewee table classes to be checked.

        Returns:
            bool: True if any provided table contains data, False otherwise.

        Raises:
            PeeweeException: If a Peewee-specific error occurs during the query.
        """
        try:
            return any(table.select().exists() for table in tables)
        except PeeweeException as e:
            logger.error(f"Failed to check data: {e}")
            raise
