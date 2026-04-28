"""Representation of a file."""

from peewee import Model, SqliteDatabase, TextField

from halper.utils import settings


class File(Model):
    """Files model."""

    name = TextField()
    path = TextField()

    def __str__(self) -> str:  # pragma: no cover
        """Return string representation of file."""
        return f"{self.__data__}"

    class Meta:
        """Meta class for base model."""

        database = SqliteDatabase(settings.db_path, regexp_function=True)


class TempFile(Model):
    """Temporary files model."""

    name = TextField()
    path = TextField()

    class Meta:
        """Meta class for base model."""

        database = SqliteDatabase(settings.db_path, regexp_function=True)
