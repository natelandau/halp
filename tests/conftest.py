# type: ignore
"""Shared fixtures for tests."""

import shutil
from pathlib import Path

import pytest
from peewee import SqliteDatabase

from halp.utils import console  # isort:skip
from halp.models import (
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
def fixture_file(tmp_path):
    """Create a fixture file for testing."""

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


@pytest.fixture()
def mock_config_get(mocker, tmp_path):
    """Returns a mock configuration for use in tests."""

    def mock_config_inner(config: dict | None = None):
        """Returns a mock configuration for use in tests."""
        default_mock_config = {
            "file_globs": [f"{tmp_path}/dotfiles/*.bash"],
            "file_exclude_regex": ".*ignore.*",
            "case_sensitive": False,
            "categories": {
                "hello": {
                    "category_name": "hello world",
                    "code_regex": r"hello.*world",
                    "comment_regex": r"",
                    "description": "hello world category",
                    "name_regex": "",
                    "path_regex": "",
                }
            },
        }

        if not config:
            config = default_mock_config
        # Mock the CONFIG.get method
        mock_get = mocker.patch("halp.models.indexer.CONFIG.get")
        # mock_get = mocker.patch("halp.models.parser.CONFIG.get")
        # mock_get = mocker.patch("halp.cli.CONFIG.get")
        # Configure the mock to return specific values based on the called arguments
        mock_get.side_effect = lambda key, default=None, pass_none=False: config.get(key, default)

        return mock_get

    return mock_config_inner
