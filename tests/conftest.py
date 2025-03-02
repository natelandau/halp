# type: ignore
"""Fixtures for testing."""

import re
from collections.abc import Callable
from pathlib import Path
from textwrap import dedent

import pytest
from playhouse.sqlite_ext import SqliteExtDatabase
from rich.console import Console

from halper.utils.database import HalpInfo  # isort: skip
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

console = Console()


@pytest.fixture
def fixture_file(tmp_path: Path) -> Callable[[str], Path]:
    """Create a fixture that provides a function for generating test files with custom content.

    Create a reusable test file generator that writes provided text content to a temporary file. This fixture is useful for testing file parsing, reading, and processing functionality without creating permanent files on disk. The temporary file is automatically cleaned up after each test.

    Args:
        tmp_path (Path): Pytest fixture providing a temporary directory path

    Returns:
        Callable[[str], Path]: A function that accepts a text string and returns the path
            to the created temporary file. The function has signature:
        text (str, optional): Content to write to the file. Defaults to "sample text".

    Example:
        def test_file_parser(fixture_file):
            test_file = fixture_file("alias ls='ls -la'")
            parser = Parser(test_file)
            assert parser.parse() is not None
    """

    def _method(text: str = "sample text") -> Path:
        """Create a temporary file with the provided text content and return its path.

        Create a file in a temporary directory and write the given text content to it. This is useful for testing file operations without creating permanent files on disk. The file will be automatically cleaned up after the test completes.

        Args:
            text (str): The content to write to the temporary file. Defaults to "sample text".

        Returns:
            Path: The path to the created temporary file.
        """
        test_file = tmp_path / "test_file"
        test_file.write_text(text)

        return test_file

    return _method


@pytest.fixture
def clean_stdout(capsys: pytest.CaptureFixture[str]) -> Callable[[], str]:
    r"""Return a function that cleans ANSI escape sequences from captured stdout.

    This fixture is useful for testing CLI output where ANSI color codes and other escape sequences need to be stripped to verify the actual text content. The returned callable captures stdout using pytest's capsys fixture and removes all ANSI escape sequences, making it easier to write assertions against the cleaned output.

    Args:
        capsys (pytest.CaptureFixture[str]): Pytest fixture that captures stdout/stderr streams

    Returns:
        Callable[[], str]: A function that when called returns the current stdout with all ANSI escape sequences removed

    Example:
        def test_cli_output(clean_stdout):
            print("\033[31mRed Text\033[0m")  # Colored output
            assert clean_stdout() == "Red Text"  # Test against clean text
    """
    ansi_chars = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")

    def _get_clean_stdout() -> str:
        return ansi_chars.sub("", capsys.readouterr().out)

    return _get_clean_stdout


@pytest.fixture
def debug() -> Callable[[str | Path, str, bool, int], bool]:
    """Return a debug printing function for test development and troubleshooting.

    Create and return a function that prints formatted debug output to the console during test development and debugging. The returned function allows printing variables, file contents, or directory structures with clear visual separation and optional breakpoints.

    Returns:
        Callable[[str | Path, str, bool, int], bool]: A function that prints debug info with
            the following parameters:
            - value: The data to debug print (string or Path)
            - label: Optional header text for the output
            - breakpoint: Whether to pause execution after printing
            - width: Maximum output width in characters

    Example:
        def test_complex_data(debug):
            result = process_data()
            debug(result, "Processed Data", breakpoint=True)
    """

    def _debug_inner(
        value: str | Path, label: str = "", breakpoint: bool = False, width: int = 80
    ) -> bool:
        """Print debug information during test development and debugging sessions.

        Print formatted debug output to the console with optional breakpoints. This is particularly useful when developing or debugging tests to inspect variables, file contents, or directory structures. The output is formatted with a labeled header and footer rule for clear visual separation.

        Args:
            value (Union[str, Path]): The value to debug print. If a Path to a directory is provided, recursively prints all files in that directory tree.
            label (str): Optional header text to display above the debug output for context.
            breakpoint (bool, optional): If True, raises a pytest.fail() after printing to pause execution. Defaults to False.
            width (int, optional): Maximum width in characters for the console output. Matches pytest's default width of 80 when running without the -s flag. Defaults to 80.

        Returns:
            bool: Always returns True unless breakpoint=True, in which case raises pytest.fail()

        Example:
            def test_something(debug):
                # Print contents of a directory
                debug(Path("./test_data"), "Test Data Files")

                # Print a variable with a breakpoint
                debug(my_var, "Debug my_var", breakpoint=True)
        """
        console.rule(label or "")

        # If a directory is passed, print the contents
        if isinstance(value, Path) and value.is_dir():
            for p in value.rglob("*"):
                console.print(p, width=width)
        else:
            console.print(value, width=width)

        console.rule()

        if breakpoint:
            return pytest.fail("Breakpoint")

        return True

    return _debug_inner


@pytest.fixture
def populate_db():
    """Create test database fixtures and clean up after test execution.

    Create a populated test database with sample commands, categories and relationships for testing.

    This fixture uses pytest's yield fixture pattern to clean up the database after each test, ensuring tests start with a clean state. Use this fixture in tests that need to query or manipulate a populated database.

    Yields:
        None: This fixture yields control to the test and cleans up afterwards
    """
    # First, clear existing data
    Category.delete().execute()
    File.delete().execute()
    Command.delete().execute()
    CommandCategory.delete().execute()

    # Then, create new data
    file = File.create(name="test", path="test")
    cat1 = Category.create(name="cat1")
    cat2 = Category.create(name="cat2")

    alias1 = Command.create(
        name="alias1",
        code="alias='alias1 #one' ",
        description="alias1 description",
        command_type="alias",
        file=file,
    )
    CommandCategory.create(command=alias1, category=cat1)

    alias2 = Command.create(
        name="alias2",
        code="alias='alias2 #this is the second' ",
        description="alias2 description",
        command_type="alias",
        file=file,
    )
    CommandCategory.create(command=alias2, category=cat1)

    alias3 = Command.create(
        name="alias3",
        code="alias='alias3' #this is the third alias",
        description="alias3 description",
        command_type="alias",
        file=file,
    )
    CommandCategory.create(command=alias3, category=cat2)

    alias3 = Command.create(
        name="alias4",
        code="alias='alias4' #this is the fourth alias",
        description="alias4",
        command_type="alias",
        hidden=True,
        file=file,
    )
    CommandCategory.create(command=alias3, category=cat2)

    func1 = Command.create(
        name="func1", code="func1", description="func1", command_type="function", file=file
    )
    CommandCategory.create(command=func1, category=cat1)

    func2 = Command.create(
        name="func2", code="func2", description="func2", command_type="function", file=file
    )
    CommandCategory.create(command=func2, category=cat2)

    export1 = Command.create(
        name="export1", code="export1", description="export1", command_type="export", file=file
    )
    CommandCategory.create(command=export1, category=cat2)

    export2 = Command.create(
        name="export2", code="export2", description="export2", command_type="export", file=file
    )
    CommandCategory.create(command=export2, category=cat2)

    yield  # Allow the test to run

    # Clean up after the test
    Category.delete().execute()
    File.delete().execute()
    Command.delete().execute()
    CommandCategory.delete().execute()


@pytest.fixture(autouse=True)
def mock_db(request) -> SqliteExtDatabase | None:
    """Create and manage an isolated in-memory SQLite test database.

    Create a temporary SQLite database in memory that automatically resets between test runs. This fixture provides a clean, isolated database environment for each test to prevent test pollution and avoid modifying the production database.

    The database is configured with:
    - SQLite regexp function enabled for pattern matching
    - Core models pre-bound but with foreign key and backref binding disabled
    - Automatic table creation for all required models
    - Full cleanup after each test

    This fixture is essential for testing database operations as it:
    - Ensures consistent starting state for each test
    - Prevents tests from interfering with each other
    - Avoids any disk I/O by using in-memory storage
    - Handles all setup and teardown automatically

    Args:
        request (pytest.FixtureRequest): Pytest fixture request object to check for no_db marker

    Yields:
        SqliteExtDatabase | None: Configured database connection with tables:
            - Category: Store command categories
            - Command: Store shell commands
            - CommandCategory: Map commands to categories
            - File: Track source files
            - HalpInfo: Store version information

    Example:
        def test_db_operation(mock_db):
            # Database starts clean for each test
            Category.create(name="test")
            assert Category.select().count() == 1
            # Database is automatically reset after test

    Note:
        Skip this fixture by marking tests with @pytest.mark.no_db() when database
        access is not needed.
    """
    if "no_db" in request.keywords:
        # when '@pytest.mark.no_db()' is called, this fixture will not run
        yield
    else:
        models = [
            Category,
            Command,
            CommandCategory,
            File,
            HalpInfo,
            TempCategory,
            TempCommand,
            TempCommandCategory,
            TempFile,
        ]

        db = SqliteExtDatabase(":memory:", regexp_function=True)
        db.bind(models, bind_refs=False, bind_backrefs=False)
        # Ensure we start with a fresh connection
        if not db.is_closed():
            db.close()

        db.connect()
        db.create_tables(models)

        yield db

        db.close()


@pytest.fixture
def mock_config(debug, tmp_path):
    """Create a fixture that provides a mock configuration function for testing.

    Create a function that allows overriding default configuration settings during tests. The returned function accepts keyword arguments to override specific settings while preserving defaults for unspecified values. This enables testing configuration-dependent functionality in isolation without modifying actual config files.

    The mock config function handles common settings like file globs, comment placement, and regex patterns. All overridden values are converted to uppercase to match the expected configuration format.

    Args:
        debug (Callable): Debug logging function for inspecting override values

    Returns:
        Callable[[**kwargs], dict[str, Any]]: A function that accepts arbitrary keyword arguments and returns a dictionary containing the merged configuration settings. The returned dict has uppercase keys and preserves default values for any unspecified settings.

    Example:
        def test_search_command(mock_config):

            # Override file globs while keeping other defaults
            settings.update(mock_config(file_globs=["*.py"]))
            with pytest.raises(cappa.Exit):
                cappa.invoke(obj=Halp, argv=["-vv", "search", "func2"])
    """

    def _inner(**kwargs):
        """Create a configuration dictionary by merging provided overrides with default settings.

        Takes arbitrary configuration overrides and merges them with default settings, converting keys to uppercase to match the expected format. This inner function enables test-specific configuration by allowing selective override of settings while maintaining defaults for unspecified values.

        Args:
            **kwargs: Configuration key-value pairs to override.

        Returns:
            dict[str, Any]: Configuration dictionary with uppercase keys containing merged default and override values
        """
        stub_settings = {
            "COMMAND_NAME_IGNORE_REGEX": "",
            "COMMENT_PLACEMENT": "best",
            "FILE_EXCLUDE_REGEX": "",
            "FILE_GLOBS": [],
            "CATEGORIES": {},
            "DB_PATH": ":memory:",
        }

        override_data = {key: value for key, value in kwargs.items() if value is not None}

        for key, value in override_data.items():
            # Convert key to uppercase to match stub_settings format
            upper_key = key.upper()
            if upper_key in stub_settings:
                stub_settings[upper_key] = value

        return stub_settings

    return _inner


@pytest.fixture
def mock_files(tmp_path) -> Path:
    """Create a temporary directory structure with mock shell script files for testing.

    Create a standardized test environment with shell script files containing aliases, functions and exports in different comment styles. This fixture helps test the command parser's ability to handle various shell constructs and comment placements.

    The created structure:
        root/
        ├── dir1/
        │   └── aliases.sh    # Contains alias definitions
        ├── dir2/
        │   └── functions.sh  # Contains shell functions
        └── exports.sh        # Contains export statements

    Args:
        tmp_path (Path): Pytest fixture providing a temporary directory path

    Returns:
        Path: Path to the root directory containing the mock file structure
    """
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    dir1 = root_dir / "dir1"
    dir1.mkdir()
    dir2 = root_dir / "dir2"
    dir2.mkdir()

    file1_text = dedent("""
        alias no_comment='echo "Hello, No Comment!"'
        alias inline='echo "Hello, Inline!"' # inline comment

        # above comment
        alias above='echo "Hello, Above!"'
    """)

    (dir1 / "aliases.sh").write_text(file1_text)

    file2_text = dedent("""
        func_no_comment() {
            echo "Hello, no comment!"
        }

        # above comment
        func_above() {
            echo "Hello, Above!"
        }

        func_inline() {
            # inline comment
            echo "Hello, Inline!"
        }
    """)
    (dir2 / "functions.sh").write_text(file2_text)

    file3_text = dedent("""
        export NO_COMMENT="Hello, No Comment!"

        # above comment
        export ABOVE="Hello, Above!"

        export INLINE="Hello, Inline!" # inline comment
    """)
    (root_dir / "exports.sh").write_text(file3_text)

    return root_dir
