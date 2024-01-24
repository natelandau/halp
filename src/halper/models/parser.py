"""Parses files for commands and adds them to the database."""

import re
from pathlib import Path

from loguru import logger
from parsy import ParseError

from halper.config import HalpConfig
from halper.models import Category, File
from halper.utils.text_parsers import parse_file


class Parser:
    """Extract shell script components from files and categorize them for database storage.

    This class handles parsing of command files, extracting relevant details like command names,
    code, and descriptions. It then categorizes these commands based on predefined patterns in
    the configuration before updating the database with this information.
    """

    def __init__(self, path: Path | str) -> None:
        """Initialize the parser with a file path.

        Resolve the provided file path and set up the parser to process the file. Initialize
        the case sensitivity for regex matching based on configuration settings.

        Args:
            path (Path | str): The path of the file to parse.
        """
        if isinstance(path, str):
            path = Path(path)

        self.path = path.expanduser().resolve()
        self.regex_flags = 0 if HalpConfig().case_sensitive else re.IGNORECASE
        self.file = self._fetch_file_record()

    def _fetch_file_record(self) -> File:
        """Retrieve or create a file record in the database for the current file.

        Check the database for an existing record of the file. If not found, create a new record.

        Returns:
            File: The database record corresponding to the current file.
        """
        file, created = File.get_or_create(
            name=self.path.name,
            path=str(self.path),
            defaults={},
        )

        if created:
            logger.debug(f"Added file '{file.name}' to database")
        else:
            logger.trace(f"File '{file.name}' already exists in database")

        return file

    def _categorize_command(self, result: dict[str, str]) -> list[Category]:
        """Categorize a command based on regex patterns defined in categories.

        Use the provided command details to match against category regex patterns. If a command
        matches a category pattern, categorize the command accordingly.

        Args:
            result (dict[str, str]): The parsed command details.

        Returns:
            list[Category]: A list of categories that the command belongs to.
        """
        matched_categories: list[Category] = []
        categories = Category.select()

        for cat in categories:
            for pattern, text in [
                (cat.code_regex, result["code"]),
                (cat.comment_regex, result["description"]),
                (cat.command_name_regex, result["name"]),
                (cat.path_regex, str(self.path)),
            ]:
                if pattern and text and re.search(pattern, text, flags=self.regex_flags):
                    matched_categories.append(cat)
                    break

        if matched_categories:
            return matched_categories

        default_cat, _ = Category.get_or_create(
            name=HalpConfig().uncategorized_name, defaults={"description": "Uncategorized commands"}
        )
        return [default_cat]

    def parse(self) -> list:
        """Parse the file and update the database with extracted command details.

        Read the file, extract command details, categorize them, and compile a list of commands
        with their associated categories. Ignore commands based on the ignore regex from the configuration.

        Returns:
            list: A list of dictionaries, each representing a parsed command with its details.
        """
        # Ignore commands that match the ignore regex
        command_name_ignore_regex = HalpConfig().command_name_ignore_regex

        categorized_commands: list[dict] = []

        # Parse the file
        try:
            results = parse_file.many().parse(self.path.read_text())
        except ParseError as e:
            logger.trace(f"No commands found in file {self.path}: {e}")
            return categorized_commands

        for result in results:
            # Pass over commands that match the ignore regex
            if command_name_ignore_regex and re.search(
                command_name_ignore_regex, result["name"], flags=self.regex_flags
            ):
                logger.trace(f"Ignored command '{result['name']}' in {self.path}")
                continue

            # Find categories for command
            result["categories"] = self._categorize_command(result)
            result["file"] = self.file
            categorized_commands.append(result)

        return categorized_commands
