"""Command to (re)create the index of commands."""

import glob
import re
from pathlib import Path

import typer
from loguru import logger
from peewee import PeeweeException
from rich.progress import track
from rich.table import Table

from halper.constants import CONFIG, DB
from halper.models import (
    Category,
    Command,
    CommandCategory,
    Database,
    File,
    Parser,
    TempCategory,
    TempCommand,
    TempCommandCategory,
    TempFile,
)
from halper.utils import console, errors


class Indexer:
    """Indexer class for creating and rebuilding the index of commands from configuration and file data.

    Initialize the indexer to create or rebuild the index of commands. The indexer scans for command files based on the configuration settings and updates the database accordingly.

    Args:
        rebuild (bool, optional): Specify whether to rebuild the index from scratch. Defaults to False.
    """

    def __init__(self, rebuild: bool = False) -> None:
        self.globs: list[str] = CONFIG.get("file_globs")
        self.exclude_regex: str = CONFIG.get("file_exclude_regex", default="")
        self.case_sensitive: bool = CONFIG.get("case_sensitive", False)
        self.database = Database(DB)

        # Set rebuild flag
        self.rebuild: bool = rebuild

        # If no data in the database, set rebuild flag to True. Useful for first run.
        if not self.rebuild:
            self.rebuild = not self.database.has_data([Command])

    def _add_files(self) -> list[tuple[str, str, str]]:
        """Search for and add files to the database based on user-defined glob patterns.

        Returns a tuple representing the status of file addition to be displayed in the indexing summary.

        Returns:
            list[tuple[str, str, str]]: A list of tuples containing status indicators and messages for file indexing.
        """
        case_sensitive_regex = 0 if self.case_sensitive else re.IGNORECASE
        files = []
        return_strings = []

        for user_glob in self.globs:
            # Expand '~' to home directory
            glob_path = re.sub(r"^~", str(Path.home()), user_glob)

            logger.debug(f"Searching for files matching: {glob_path}")

            found_files = glob.glob(glob_path, recursive=True)  # noqa: PTH207
            if not found_files:
                return_strings.append(("🤷", "", f"[dim]Glob found no files: {user_glob}[/dim]"))
                continue
            files.extend([Path(x) for x in found_files])

        files = [
            file
            for file in files
            if file.is_file()
            and (
                not self.exclude_regex
                or not re.search(self.exclude_regex, str(file), flags=case_sensitive_regex)
            )
        ]

        if not files:
            raise errors.NoFilesFoundError

        for file in files:
            File.get_or_create(name=file.name, path=file)
        return_strings.insert(0, ("✅", f"{File.select().count()}", "Files parsed"))
        return return_strings

    @staticmethod
    def _persist_command_settings() -> None:
        """Update the database with the hidden status of commands from the temporary command settings."""
        # Persist hidden status for existing commands

        matching_commands = TempCommand.select(
            TempCommand.name, TempCommand.code, TempCommand.hidden
        ).where(TempCommand.hidden == True)  # noqa: E712

        for temp_command in matching_commands:
            update_query = Command.update(hidden=temp_command.hidden).where(
                (Command.name == temp_command.name) & (Command.code == temp_command.code)
            )
            update_query.execute()
            logger.debug(f"Updated hidden status for: {temp_command.name}")

    @staticmethod
    def _command_output() -> list[tuple[str, str, str]]:
        """Generate a summary of command indexing for display in the command table.

        Returns:
            list[tuple[str, str, str]]: A list of tuples containing status indicators and messages for command indexing.
        """
        return_result = []

        num_commands = Command.select().count()
        if num_commands == 0:
            return_result.append(("❌", "", "No commands indexed"))
        else:
            return_result.append(("✅", f"{num_commands}", "Commands indexed"))

        return return_result

    @staticmethod
    def _add_categories() -> tuple[str, str, str]:
        """Add categories from the configuration file to the database.

        Processes and inserts categories defined in the configuration into the database.

        Returns:
            tuple[str, str, str]: Status indicator, count of categories added, and a descriptive message.
        """
        # Grab categories from the configuration file and rename keys to match database
        config_categories: list[dict[str, str]] = [  # type: ignore [var-annotated]
            {("name" if k == "category_name" else k): v for k, v in d.items()}
            for d in CONFIG.get("categories", default={}).values()
        ]

        # Add categories to the database
        with DB.atomic():
            num_categories = Category.insert_many(config_categories).execute()

        logger.debug(f"Added {num_categories} categories from config")

        if not num_categories or num_categories == 0:
            return ("❓", "", "No categories from config")

        return ("✅", f"{num_categories}", "Categories from config")

    @staticmethod
    def _add_commands(command_list: list[dict]) -> int:
        """Insert a list of command details into the database.

        Args:
            command_list (list[dict]): List of command details to be added.

        Returns:
            int: The number of commands successfully added to the database.
        """
        for command in command_list:
            with DB.atomic():
                row = Command.insert(
                    name=command["name"],
                    code=command["code"],
                    file=command["file"],
                    command_type=command["command_type"].name,
                    description=command["description"],
                ).execute()

                CommandCategory.insert_many([
                    {"command": row, "category": category} for category in command["categories"]
                ]).execute()

        return len(command_list)

    @staticmethod
    def _create_temporary_tables() -> None:
        """Create temporary tables for storing file and category data during the indexing process."""
        with DB.atomic() as transaction:
            try:
                # Create temporary tables
                TempFile.create_table(safe=True)
                TempCategory.create_table(safe=True)
                TempCommand.create_table(safe=True)
                TempCommandCategory.create_table(safe=True)

                # Copy data to TempFile
                for file in File.select():
                    TempFile.create(name=file.name, path=file.path)

                # Copy data to TempCategory
                for category in Category.select():
                    TempCategory.create(
                        name=category.name,
                        description=category.description,
                        code_regex=category.code_regex,
                        comment_regex=category.comment_regex,
                        name_regex=category.name_regex,
                        path_regex=category.path_regex,
                    )

                # Copy data to TempCommand
                for command in Command.select():
                    TempCommand.create(
                        code=command.code,
                        command_type=command.command_type,
                        description=command.description,
                        file=TempFile.get_or_none(TempFile.path == command.file.path) or None,
                        name=command.name,
                        hidden=command.hidden,
                    )

                # Copy data to TempCommandCategory
                for command_category in CommandCategory.select():
                    temp_command = TempCommand.get(
                        TempCommand.name == command_category.command.name
                    )
                    temp_category = TempCategory.get(
                        TempCategory.name == command_category.category.name
                    )
                    TempCommandCategory.create(command=temp_command, category=temp_category)

            except PeeweeException:  # pragma: no cover
                # Rollback the transaction in case of an error
                transaction.rollback()
                raise  # You might want to handle or log this exception

    @staticmethod
    def _drop_temporary_tables() -> None:
        """Remove temporary tables used during the indexing process."""
        with DB.atomic() as transaction:
            try:
                TempCommandCategory.drop_table()
                TempCommand.drop_table()
                TempCategory.drop_table()
                TempFile.drop_table()
            except PeeweeException:  # pragma: no cover
                # Rollback the transaction in case of an error
                transaction.rollback()
                raise  # You might want to handle or log this exception

    def do_index(self) -> None:
        """Execute the indexing process to create or update the command index in the database.

        Manages the indexing workflow including setting up temporary tables, clearing existing data,
        processing files and categories, and cleaning up after indexing.
        """
        # Setup table
        grid = Table.grid(expand=False, padding=(0, 1))
        grid.add_column()
        grid.add_column()
        grid.add_column()
        grid_rows = []

        # Create temporary tables and clear production database entries
        if not self.rebuild:
            self._create_temporary_tables()

        # Clear production database entries
        self.database.clear_data([File, Category, Command, CommandCategory])

        # Add categories to the database
        result = self._add_categories()
        grid_rows.append(result)

        # Add files to the database
        try:
            files_result = self._add_files()
            grid_rows.extend(files_result)
        except errors.NoFilesFoundError as e:
            logger.error("No files found matching the globs in your configuration.")
            raise typer.Exit(code=1) from e

        # Add commands to the database
        for file in track(File.select(), description="Processing files...", transient=True):
            p = Parser(file.path)
            found_commands = p.parse()
            if not found_commands:
                grid_rows.append(("🤷", "", f"[dim]No commands found in '{file.path}'"))
                continue
            self._add_commands(found_commands)
            logger.debug(f"Add {len(found_commands)} commands from '{file.path}'")

        if not self.rebuild:
            self._persist_command_settings()

        # Build details on command updates
        grid_rows.extend(list(self._command_output()))

        # Cleanup
        if not self.rebuild:
            self._drop_temporary_tables()

        # Print table
        for row in grid_rows:
            grid.add_row(*row)

        title = "Rebuilding index of commands" if not self.rebuild else "Indexing commands"
        console.print(f"[bold italic underline]{title}[/bold italic underline]", justify="center")
        console.print(grid)
