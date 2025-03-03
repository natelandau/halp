"""Command to (re)create the index of commands."""

import glob
import re
from pathlib import Path

import cappa
from playhouse.sqlite_ext import SqliteExtDatabase
from rich.progress import track

from halper.models import (
    Category,
    Command,
    CommandCategory,
    File,
    IndexResult,
    Parser,
    TempCategory,
    TempCommand,
    TempCommandCategory,
    TempFile,
)
from halper.utils import db_clear_table_data, db_tables_have_data, errors, pp, settings


class Indexer:
    """Indexer class for creating and rebuilding the index of commands from configuration and file data.

    Initialize the indexer to create or rebuild the index of commands. The indexer scans for command files based on the configuration settings and updates the database accordingly.

    Args:
        rebuild (bool, optional): Specify whether to rebuild the index from scratch. Defaults to False.
    """

    def __init__(self, *, rebuild: bool = False) -> None:
        self.database = SqliteExtDatabase(settings.db_path, regexp_function=True)
        self.result = IndexResult()

        # Set rebuild flag
        self.rebuild: bool = rebuild

        # If no data in the database, set rebuild flag to True. Useful for first run.
        if not self.rebuild:
            self.rebuild = not db_tables_have_data([Command])

    def _add_files(self) -> None:
        """Search for and add files to the database based on user-defined glob patterns.

        Raises:
            errors.NoFilesFoundError: If no files are found matching the globs.
        """
        files = []

        for user_glob in settings.file_globs:
            # Expand '~' to home directory
            glob_path = re.sub(r"^~", str(Path.home()), user_glob)

            pp.trace(f"Searching for files matching: {glob_path}")

            found_files = glob.glob(glob_path, recursive=True)  # noqa: PTH207

            if not found_files:
                self.result.glob_paths[user_glob] = 0
                continue
            files.extend([Path(x) for x in found_files])
            self.result.glob_paths[user_glob] = len(found_files)
        files = [
            file
            for file in files
            if file.is_file()
            and (
                not settings.file_exclude_regex
                or not re.search(settings.file_exclude_regex, str(file), flags=re.IGNORECASE)
            )
        ]

        if not files:
            raise errors.NoFilesFoundError

        for file in files:
            File.get_or_create(name=file.name, path=file)

    @staticmethod
    def _persist_command_settings() -> None:
        """Update the database with user configurable data from the temporary command settings."""
        # Find commands with values to persist
        commands_to_persist = TempCommand.select().where(
            (TempCommand.hidden == True) | (TempCommand.has_custom_description == True)  # noqa: E712
        )

        for c in commands_to_persist:
            # Update commands
            if c.hidden and not c.has_custom_description:
                update_type = "hidden status"
                num_rows = (
                    Command.update(hidden=c.hidden)
                    .where(
                        (Command.name == c.name)
                        & (Command.code == c.code)
                        & (Command.file == c.file)
                        & (Command.description == c.description)
                    )
                    .execute()
                )

            elif c.hidden and c.has_custom_description:
                update_type = "hidden status and custom description"
                num_rows = (
                    Command.update(
                        hidden=c.hidden,
                        description=c.description,
                        has_custom_description=c.has_custom_description,
                    )
                    .where(
                        (Command.name == c.name)
                        & (Command.code == c.code)
                        & (Command.file == c.file)
                    )
                    .execute()
                )

            elif not c.hidden and c.has_custom_description:
                update_type = "custom description"
                num_rows = (
                    Command.update(
                        description=c.description,
                        has_custom_description=c.has_custom_description,
                    )
                    .where(
                        (Command.name == c.name)
                        & (Command.code == c.code)
                        & (Command.file == c.file)
                    )
                    .execute()
                )

            if num_rows > 1:
                pp.trace(f"Persist {update_type} for: {c.name}. {num_rows} commands matched.")
            else:
                pp.trace(f"Persist {update_type} for: {c.name}")

        # Persist custom categories for existing commands
        command_cats_to_persist = TempCommandCategory.select().where(
            TempCommandCategory.is_custom == True  # noqa: E712
        )

        for c in command_cats_to_persist:
            command = Command.get_or_none(
                (Command.name == c.command.name)
                & (Command.code == c.command.code)
                & (Command.file == c.command.file)
                & (Command.description == c.command.description)
                & (Command.hidden == c.command.hidden)
                & (Command.has_custom_description == c.command.has_custom_description)
            )
            category = Category.get_or_none(name=c.category.name)

            if not command or not category:
                continue

            # Delete auto-assigned categories
            CommandCategory.delete().where(
                (CommandCategory.command == command) & (CommandCategory.category != category)
            ).execute()

            # Add custom category
            CommandCategory.create(command=command, category=category, is_custom=True)

            pp.trace(f"Persist custom category for: {c.command.name}")

        pp.debug("Merged old and new data")

    def _add_categories(self) -> None:
        """Add categories from the configuration file to the database.

        Processes and inserts categories defined in the configuration into the database.
        """
        if not settings.categories:
            return

        config_categories = list(settings.categories.values())
        pp.trace(f"Indexing categories: {[x.name for x in config_categories]}")

        Category.insert_many(config_categories).execute()
        self.result.categories.extend([x.name for x in config_categories])

    @staticmethod
    def _add_commands(command_list: list[dict]) -> int:
        """Insert a list of command details into the database.

        Args:
            command_list (list[dict]): List of command details to be added.

        Returns:
            int: The number of commands successfully added to the database.
        """
        for command in command_list:
            row = Command.insert(
                name=command["name"],
                code=command["code"],
                file=command["file"],
                command_type=command["command_type"].name,
                description=command["description"],
            ).execute()

            CommandCategory.insert_many(
                [{"command": row, "category": category} for category in command["categories"]]
            ).execute()

        return len(command_list)

    def _create_temporary_tables(self) -> None:
        """Create temporary tables for storing file and category data during the indexing process."""
        if TempFile.table_exists():
            self._drop_temporary_tables()

        # Create temporary tables
        TempFile.create_table(safe=True)
        TempCategory.create_table(safe=True)
        TempCommand.create_table(safe=True)
        TempCommandCategory.create_table(safe=True)

        # Copy data to TempFile
        tmp_files_to_insert = [TempFile(name=file.name, path=file.path) for file in File.select()]
        with self.database.atomic():
            TempFile.bulk_create(tmp_files_to_insert, batch_size=100)

        # Copy data to TempCategory
        tmp_categories_to_insert = [
            TempCategory(
                name=category.name,
                description=category.description,
                code_regex=category.code_regex,
                comment_regex=category.comment_regex,
                command_name_regex=category.command_name_regex,
                path_regex=category.path_regex,
            )
            for category in Category.select()
        ]
        with self.database.atomic():
            TempCategory.bulk_create(tmp_categories_to_insert, batch_size=100)

        # Copy data to TempCommand
        tmp_commands_to_insert = [
            TempCommand(
                code=command.code,
                command_type=command.command_type,
                description=command.description,
                file=TempFile.get_or_none(TempFile.path == command.file.path) or None,
                name=command.name,
                hidden=command.hidden,
                has_custom_description=command.has_custom_description,
            )
            for command in Command.select()
        ]
        with self.database.atomic():
            TempCommand.bulk_create(tmp_commands_to_insert, batch_size=100)

        # Copy data to TempCommandCategory
        tmp_command_cats_to_insert = [
            TempCommandCategory(
                command=TempCommand.get(
                    TempCommand.name == command_cat.command.name,
                    TempCommand.code == command_cat.command.code,
                ),
                category=TempCategory.get(TempCategory.name == command_cat.category.name),
                is_custom=command_cat.is_custom,
            )
            for command_cat in CommandCategory.select()
        ]
        with self.database.atomic():
            TempCommandCategory.bulk_create(tmp_command_cats_to_insert, batch_size=100)

        pp.debug("Transferred data to temporary tables")

    @staticmethod
    def _drop_temporary_tables() -> None:
        """Remove temporary tables used during the indexing process."""
        TempCommandCategory.drop_table()
        TempCommand.drop_table()
        TempCategory.drop_table()
        TempFile.drop_table()
        pp.debug("Dropped temporary tables")

    def do_index(self) -> None:
        """Index commands from configured files into the database.

        Execute a full indexing workflow to discover and store commands from source files. The workflow:
        1. Creates temporary tables to preserve existing command settings during rebuild
        2. Clears existing database entries
        3. Loads configured categories
        4. Scans and indexes files matching configured globs
        5. Parses each file to extract commands
        6. Persists command settings from temporary tables if not rebuilding
        7. Cleans up temporary tables

        This function enables maintaining an up-to-date searchable index of commands as source files change. Run this after modifying command files or changing the configuration.

        Raises:
            cappa.Exit: If no files are found matching the configured globs.
        """
        # Create temporary tables and clear production database entries
        if not self.rebuild:
            self._create_temporary_tables()

        # Clear production database entries
        db_clear_table_data([File, Category, Command, CommandCategory])

        # Add categories to the database
        self._add_categories()

        # Add files to the database
        try:
            self._add_files()
        except errors.NoFilesFoundError as e:
            pp.error("No files found matching the globs in your configuration.")
            raise cappa.Exit(code=1) from e

        # Add commands to the database
        for file in track(File.select(), description="Processing files...", transient=True):
            p = Parser(file.path)

            found_commands = p.parse()
            self.result.files[Path(file.path)] = len(found_commands)
            if not found_commands:
                continue
            self._add_commands(found_commands)
            pp.trace(f"Add {len(found_commands)} commands from '{file.path}'")

        if not self.rebuild:
            self._persist_command_settings()

        # Build details on command updates
        self.result.total_commands = Command.select().count()

        # Cleanup
        if not self.rebuild:
            self._drop_temporary_tables()
