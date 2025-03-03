"""Representation of a command."""

from peewee import BooleanField, ForeignKeyField, Model, TextField
from playhouse.sqlite_ext import SqliteExtDatabase
from rich.syntax import Syntax
from rich.table import Table

from halper.constants import CommandType
from halper.utils import settings

from .category import Category, CommandCategory
from .file import File, TempFile


class TempCommand(Model):
    """Temporary commands model."""

    code = TextField()
    command_type = TextField()
    description = TextField(null=True)
    file = ForeignKeyField(TempFile, backref="commands", null=True)
    name = TextField(index=True)
    hidden = BooleanField(default=False)
    has_custom_description = BooleanField(default=False)

    class Meta:
        """Meta class for base model."""

        database = SqliteExtDatabase(settings.db_path, regexp_function=True)


class Command(Model):
    """Commands model."""

    code = TextField()
    command_type = TextField()  # CommandType enum value
    description = TextField(null=True)
    file = ForeignKeyField(File, backref="commands", null=True)
    name = TextField(index=True)
    hidden = BooleanField(default=False)
    has_custom_description = BooleanField(default=False)

    def __str__(self) -> str:  # pragma: no cover
        """Return string representation of command."""
        return f"{self.__data__}"

    @property
    def escaped_desc(self) -> str:
        """Return escaped description."""
        return self.description.replace("[", "\\[") if self.description else ""

    @property
    def category_names(self) -> list[str]:
        """Return a list of category names associated with this command.

        Retrieve the names of categories linked to the current command instance from the database, ordered alphabetically by category name.

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

    def table(self, found_in_tldr: bool = False) -> Table:
        """Create a rich table displaying command details in a formatted layout.

        Generate a table containing comprehensive information about a command, including its name,
        ID, description, categories, type, file location, and code. The table is formatted using
        rich styling for enhanced readability in the terminal.

        Args:
            found_in_tldr (bool): Whether the command has an entry in the tldr documentation.
                If True, adds a row indicating how to view the tldr entry. Defaults to False.

        Returns:
            rich.table.Table: A formatted grid table containing command details with styled text
                and syntax highlighting for code sections.

        Note:
            This method is used by the CLI to present command information in a consistent,
            well-organized format. The table includes conditional rows for hidden commands
            and tldr availability.
        """
        grid = Table.grid(expand=False, padding=(0, 1))
        grid.add_column(style="bold")
        grid.add_column()
        grid.add_row("Command:", f"[bold]{self.name}[/bold]")
        grid.add_row("Halp ID #:", f"[cyan]{self.id!s}[/cyan]", style="dim")
        grid.add_row("Description:", self.escaped_desc)
        grid.add_row("Categories:", ", ".join(self.category_names))
        grid.add_row("Type:", self.command_type.title())
        grid.add_row("File:", f"[dim]{self.file.path}[/dim]")
        if self.hidden:
            grid.add_row("Marked as hidden:", "Yes")
        if found_in_tldr:
            grid.add_row("TLDR:", f"View TLDR entry with [code]tldr {self.name}[/code]")
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

    class Meta:
        """Meta class for base model."""

        database = SqliteExtDatabase(settings.db_path, regexp_function=True)
