# type: ignore
"""Shared fixtures for tests."""

import shutil
from pathlib import Path

import pytest
from confz import DataSource, FileSource
from peewee import SqliteDatabase

from halper.config import CategoryConfig, HalpConfig

from halper.utils import console  # isort:skip
from halper.models import (
    Category,
    Command,
    CommandCategory,
    File,
    HalpInfo,
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
    HalpInfo,
]
FIXTURE_CONFIG = Path(__file__).resolve().parent / "fixtures/configs/default_test_config.toml"
FIXTURE_DOTFILES = Path(__file__).resolve().parent / "fixtures/dotfiles"


@pytest.fixture
def mock_specific_config():
    """Mock specific configuration data for use in tests.

    Returns:
        Callable[[], list[DataSource]]: A function that returns a list of data sources.
    """

    def _inner(
        case_sensitive: bool | None = None,
        categories: dict[str, CategoryConfig] | None = None,
        command_name_ignore_regex: str | None = None,
        file_exclude_regex: str | None = None,
        file_globs: list[str] | None = None,
        uncategorized_name: str | None = None,
        comment_placement: str | None = None,
    ):
        """Collects provided arguments into a dictionary, omitting any that are None, and prepares data sources with the overridden configuration for file processing.

        Returns:
            list[DataSource]: The data sources.
        """
        # Use dictionary comprehension to filter out None values and assign to override_data
        override_data = {key: value for key, value in locals().items() if value is not None}

        return [FileSource(FIXTURE_CONFIG), DataSource(data=override_data)]

    return _inner


@pytest.fixture
def mock_config():
    """Override configuration file with mock configuration for use in tests. To override a default use the `mock_specific_config` fixture.

    Yields:
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


@pytest.fixture
def fixtures(tmp_path) -> Path:
    """Copy all directories and files from tests/fixtures into a temporary directory.

    Yields:
        Path: The temporary directory containing all fixture files.
    """
    test_dir = tmp_path / "fixtures"

    shutil.copytree(Path(__file__).resolve().parent / "fixtures", test_dir)

    yield test_dir

    shutil.rmtree(test_dir)


@pytest.fixture
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


@pytest.fixture
def debug():
    """Print debug information to the console. This is used to debug tests while writing them.

    Returns:
        Callable[[str, str | Path, bool], bool]: A function that prints debug information to the console.
    """

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
