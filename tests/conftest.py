# type: ignore
"""Shared fixtures for tests."""

import shutil
from pathlib import Path

import pytest
from confz import DataSource, FileSource
from peewee import SqliteDatabase

from halper.config import CategoryConfig, HalpConfig
from halper.constants import CommentPlacement

from halper.utils import console  # isort:skip
from halper.models import (
    Category,
    Command,
    CommandCategory,
    File,
    TempCategory,
    TempCommand,
    TempCommandCategory,
    TempFile,
)

# IMPORTANT: The MODELS list must be kept in sync with all the models defined in sr/models/database.py otherwise tests will write to the wrong database.
MODELS = [
    Command,
    Category,
    CommandCategory,
    File,
    TempFile,
    TempCommand,
    TempCategory,
    TempCommandCategory,
]
FIXTURE_CONFIG = Path(__file__).resolve().parent / "fixtures/configs/default_test_config.toml"
FIXTURE_DOTFILES = Path(__file__).resolve().parent / "fixtures/dotfiles"


@pytest.fixture()
def mock_specific_config():
    """Mock specific configuration data for use in tests."""

    def _inner(
        case_sensitive: bool | None = None,
        categories: dict[str, CategoryConfig] | None = None,
        command_name_ignore_regex: str | None = None,
        file_exclude_regex: str | None = None,
        file_globs: list[str] | None = None,
        uncategorized_name: str | None = None,
        comment_placement: str | None = None,
    ):
        override_data = {}
        if case_sensitive:
            override_data["case_sensitive"] = case_sensitive
        if file_globs:
            override_data["file_globs"] = file_globs
        if command_name_ignore_regex:
            override_data["command_name_ignore_regex"] = command_name_ignore_regex
        if comment_placement:
            override_data["comment_placement"] = comment_placement
        if file_exclude_regex:
            override_data["file_exclude_regex"] = file_exclude_regex
        if uncategorized_name:
            override_data["uncategorized_name"] = uncategorized_name
        if categories and isinstance(categories, dict):
            cats = {}
            for name, category in categories.items():
                new_cat = CategoryConfig(
                    name=category["name"],
                    code_regex=category["code_regex"],
                    comment_regex=category["comment_regex"],
                    description=category["description"],
                    command_name_regex=category["command_name_regex"],
                    path_regex=category["path_regex"],
                )
                cats[name] = new_cat
            override_data["categories"] = cats

        return [FileSource(FIXTURE_CONFIG), DataSource(data=override_data)]

    return _inner


@pytest.fixture()
def mock_config():  # noqa: PT004
    """Override configuration file with mock configuration for use in tests. To override a default use the `mock_specific_config` fixture.

    Returns:
        HalpConfig: The mock configuration.
    """
    override_data = {"file_globs": [f"{FIXTURE_DOTFILES}/**/*.bash"]}

    with HalpConfig.change_config_sources(
        [FileSource(FIXTURE_CONFIG), DataSource(data=override_data)]
    ):
        yield


@pytest.fixture(scope="class")
def mock_db() -> SqliteDatabase:
    """Create a mock database with test data for use in tests.

    The database is bound to the models, then populated with test data.
    At the end of the test, the database is closed.

    Yields:
        CSqliteExtDatabase: The mock database.
    """
    test_db = SqliteDatabase(":memory:")
    test_db.bind(MODELS, bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables(MODELS)

    yield test_db

    test_db.close()


@pytest.fixture()
def fixtures(tmp_path) -> Path:
    """Copy all directories and files from tests/fixtures into a temporary directory.

    Returns:
        Path: The temporary directory containing all fixture files.
    """
    test_dir = tmp_path / "fixtures"

    shutil.copytree(Path(__file__).resolve().parent / "fixtures", test_dir)

    yield test_dir

    shutil.rmtree(test_dir)


@pytest.fixture()
def fixture_file(tmp_path):  # noqa: D417
    """Create a single file for testing.

    Args:
        text (str): The text to write to the file.

    Returns:
        Path: The path to the file.
    """

    def _method(text: str = "sample text") -> Path:
        test_file = tmp_path / "test_file"
        test_file.write_text(text)

        return test_file

    return _method


@pytest.fixture()
def debug():
    """Print debug information to the console. This is used to debug tests while writing them."""

    def _debug_inner(label: str, value: str | Path, breakpoint: bool = False):
        """Print debug information to the console. This is used to debug tests while writing them.

        Args:
            label (str): The label to print above the debug information.
            value (str | Path): The value to print. When this is a path, prints all files in the path.
            breakpoint (bool, optional): Whether to break after printing. Defaults to False.

        Returns:
            bool: Whether to break after printing.
        """
        console.rule(label)
        if not isinstance(value, Path) or not value.is_dir():
            console.print(value)
        else:
            for p in value.rglob("*"):
                console.print(p)

        console.rule()

        if breakpoint:
            return pytest.fail("Breakpoint")

        return True

    return _debug_inner
