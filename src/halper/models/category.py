"""Representations of a category."""

from peewee import (
    BooleanField,
    DeferredForeignKey,
    ForeignKeyField,
    Model,
    TextField,
)
from playhouse.sqlite_ext import SqliteExtDatabase

from halper.utils import settings


class Category(Model):
    """Categories model."""

    name = TextField(unique=True)
    description = TextField(null=True)
    code_regex = TextField(null=True)
    comment_regex = TextField(null=True)
    command_name_regex = TextField(null=True)
    path_regex = TextField(null=True)

    def __str__(self) -> str:  # pragma: no cover
        """Return string representation of category."""
        return f"{self.__data__}"

    class Meta:
        """Meta class for base model."""

        database = SqliteExtDatabase(settings.db_path, regexp_function=True)


class TempCategory(Model):
    """Temporary categories model."""

    name = TextField(unique=True)
    description = TextField(null=True)
    code_regex = TextField(null=True)
    comment_regex = TextField(null=True)
    command_name_regex = TextField(null=True)
    path_regex = TextField(null=True)

    class Meta:
        """Meta class for base model."""

        database = SqliteExtDatabase(settings.db_path, regexp_function=True)


class CommandCategory(Model):
    """Command categories model."""

    command = DeferredForeignKey("Command", backref="categories")
    category = ForeignKeyField(Category, backref="commands")
    is_custom = BooleanField(default=False)

    def __str__(self) -> str:  # pragma: no cover
        """Return string representation of command category."""
        return f"{self.__data__}"

    class Meta:
        """Meta class for base model."""

        database = SqliteExtDatabase(settings.db_path, regexp_function=True)


class TempCommandCategory(Model):
    """Temporary command categories model."""

    command = DeferredForeignKey("TempCommand", backref="categories")
    category = ForeignKeyField(TempCategory, backref="commands")
    is_custom = BooleanField(default=False)

    class Meta:
        """Meta class for base model."""

        database = SqliteExtDatabase(settings.db_path, regexp_function=True)
