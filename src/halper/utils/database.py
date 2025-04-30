"""Database utilities for the Halper application."""

import os

from peewee import Model, PeeweeException, TextField
from playhouse.sqlite_ext import SqliteExtDatabase

from halper.models import Category, Command, CommandCategory, File

from .config import settings
from .errors import AppDirectoryError
from .printer import pp


class HalpInfo(Model):
    """HALP info model.

    This model is used to store the current application version in the database so it can be used to check for database compatibility and migrations.
    """

    version = TextField()

    class Meta:
        """Meta class for base model."""

        database = SqliteExtDatabase(settings.db_path, regexp_function=True)


def init_database(current_version: str) -> None:
    """Initialize and configure the SQLite database for storing command data.

    Create database tables for storing commands, categories, files and version info. Register custom regex function for case-sensitive/insensitive pattern matching.

    Store the current application version in the database so it can be used to check for database compatibility and migrations.

    Args:
        current_version (str): The version string to store in the database

    Raises:
        AppDirectoryError: If write permissions are not available for the database directory
        PeeweeException: If there is an error adding the version to the database

    Note:
        This function must be called before any database operations can be performed.
        The database location is determined by settings.db_path.
    """
    pp.debug(f"Instantiating database. {settings.db_path}")

    if settings.db_path != ":memory:" and not settings.db_path.parent.exists():
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check file permissions
    if settings.db_path != ":memory:" and not os.access(settings.db_path.parent, os.W_OK):
        msg = f"Write permission is not available on {settings.db_path.parent}"
        raise AppDirectoryError(msg)

    db = SqliteExtDatabase(settings.db_path, regexp_function=True)
    db.connect()

    db.create_tables([Category, Command, CommandCategory, File, HalpInfo])

    # Add current version to the database
    try:
        halp_info, created = HalpInfo.get_or_create(id=1, defaults={"version": current_version})
        if not created:
            halp_info.version = current_version
            halp_info.save()
    except PeeweeException as e:
        pp.error(f"Failed to add current version to the database: {e}")
        raise


def db_tables_have_data(tables: list[Model]) -> bool:
    """Check if any database tables contain records.

    Verify if any of the provided database tables have at least one record. This is useful for determining if a database needs initialization or if it already contains data, which helps prevent unnecessary reindexing or rebuilding of the database.

    Args:
        tables (list[Model]): List of Peewee Model classes representing database tables to check

    Returns:
        bool: True if any table contains at least one record, False if all tables are empty

    Raises:
        PeeweeException: If there is an error accessing the database tables
    """
    try:
        return any(table.select().exists() for table in tables)
    except PeeweeException as e:
        pp.error(f"Failed to check data: {e}")
        raise


def db_clear_table_data(tables: list[Model]) -> None:
    """Delete all records from specified database tables to reset their state.

    Clear all data from the provided Peewee ORM tables while maintaining the table structure. This is useful when rebuilding or reindexing the database, or when needing to start with a clean slate without dropping the tables themselves. Logs the number of records deleted from each table for auditing purposes.

    Args:
        tables (list[Model]): List of Peewee Model classes representing database tables to clear.
            Each Model class should correspond to a table in the database.

    Raises:
        PeeweeException: If deletion fails due to database errors like lock conflicts, permission issues, or connectivity problems.
    """
    try:
        for table in tables:
            delete_count = table.delete().execute()
            pp.trace(f"Cleared {delete_count} records from {table.__name__}.")
    except PeeweeException as e:
        pp.error(f"Failed to clear data from {table.__name__}: {e}")
        raise
