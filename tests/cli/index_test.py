"""Test the index subcommand."""

import re

import cappa
import pytest

from halper.constants import UNCATEGORIZED_NAME
from halper.halp import Halp
from halper.models import Category, Command, File
from halper.utils import settings

STUB_CATEGORIES = {
    "code_regex": {
        "code_regex": "inline",
        "command_name_regex": "",
        "comment_regex": "",
        "description": "Inline category description",
        "name": "code_regex",
        "path_regex": "",
    },
    "command_name_regex": {
        "code_regex": "",
        "command_name_regex": "inline",
        "comment_regex": "",
        "description": "Inline category description",
        "name": "command_name_regex",
        "path_regex": "",
    },
    "comment_regex": {
        "code_regex": "",
        "command_name_regex": "",
        "comment_regex": "inline",
        "description": "Inline category description",
        "name": "comment_regex",
        "path_regex": "",
    },
    "path_regex": {
        "code_regex": "",
        "command_name_regex": "",
        "comment_regex": "",
        "description": "Inline category description",
        "name": "path_regex",
        "path_regex": "dir2",
    },
}


@pytest.fixture(autouse=True)
def mock_initialize_subcommand(mocker, tmp_path):
    """Mock the initialization of the halp config file for testing to allow tests to run without a real config file.

    This fixture automatically runs before each test to create a temporary config file and patch the USER_CONFIG_PATH. This ensures tests have a clean, isolated config environment without affecting the real user config.
    """
    path_to_config = tmp_path / "halp.toml"
    path_to_config.touch()
    mocker.patch("halper.cli.helpers.USER_CONFIG_PATH", path_to_config)


def test_index_no_matching_files(mock_files, mock_config, clean_stdout, debug) -> None:
    """Verify that index command handles missing files gracefully."""
    # Given: Configure test environment with non-existent file pattern
    settings.update(mock_config(file_globs=[f"{mock_files}/**/*.txt"]))

    # When: Execute index command
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["index"])

    # Then: Verify error message and empty database state
    output = clean_stdout()
    assert "No files found " in output
    assert File.select().count() == 0
    assert Category.select().count() == 0
    assert Command.select().count() == 0


def test_index_no_categories(mock_files, mock_config, clean_stdout, debug) -> None:
    """Verify that index command displays all non-hidden commands with default formatting."""
    # Given: Configure test environment with populated database
    settings.update(mock_config(file_globs=[f"{mock_files}/**/*.sh"]))

    # When: Execute index command without flags
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["index"])

    # Then: Verify output shows all non-hidden commands
    output = clean_stdout()
    assert "3 Files found" in output
    assert "9 Commands indexed" in output
    assert "No categories found" in output

    assert File.select().count() == 3
    assert Category.select().count() == 1
    assert Command.select().count() == 9

    inline_alias_command = Command.get(Command.name == "inline")
    assert inline_alias_command.name == "inline"
    assert inline_alias_command.description == "inline comment"
    assert inline_alias_command.command_type == "ALIAS"
    assert inline_alias_command.code == 'echo "Hello, Inline!"'


def test_index_with_categories(mock_files, mock_config, clean_stdout, debug) -> None:
    """Verify that index command correctly categorizes commands and displays category statistics."""
    # Given: Configure test environment with categories and shell script files
    settings.update(mock_config(file_globs=[f"{mock_files}/**/*.sh"], categories=STUB_CATEGORIES))

    # When: Index all commands
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["index"])

    # Then: Verify correct number of files, commands and categories were indexed
    output = clean_stdout()
    assert "3 Files found" in output
    assert "9 Commands indexed" in output
    assert "4 Categories indexed" in output
    assert "3 Commands indexed in" not in output

    # Verify database tables contain expected record counts
    assert File.select().count() == 3
    assert Category.select().count() == 5  # 4 defined categories + 1 uncategorized
    assert Command.select().count() == 9

    # Verify sample command was indexed with correct metadata
    inline_alias_command = Command.get(Command.name == "inline")
    assert inline_alias_command.name == "inline"
    assert inline_alias_command.description == "inline comment"
    assert inline_alias_command.command_type == "ALIAS"
    assert inline_alias_command.code == 'echo "Hello, Inline!"'

    # When: List all categories
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "--cats"])

    # Then: Verify each category shows correct command count
    output = clean_stdout()
    assert re.search(r"code_regex +3", output)
    assert re.search(r"command_name_regex +3", output)
    assert re.search(r"comment_regex +3", output)
    assert re.search(r"path_regex +3", output)
    assert re.search(rf"{UNCATEGORIZED_NAME} +4", output)


def test_index_with_categories_verbose(mock_files, mock_config, clean_stdout, debug) -> None:
    """Verify that index command correctly categorizes commands and displays category statistics."""
    # Given: Configure test environment with categories and shell script files
    settings.update(mock_config(file_globs=[f"{mock_files}/**/*.sh"], categories=STUB_CATEGORIES))

    # When: Index all commands
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["-v", "index"])

    # Then: Verify correct number of files, commands and categories were indexed
    output = clean_stdout()
    debug(output)
    assert "3 Files found" in output
    assert "9 Commands indexed" in output
    assert "4 Categories indexed" in output
    assert "3 Commands indexed in" in output

    # Verify database tables contain expected record counts
    assert File.select().count() == 3
    assert Category.select().count() == 5  # 4 defined categories + 1 uncategorized
    assert Command.select().count() == 9

    # Verify sample command was indexed with correct metadata
    inline_alias_command = Command.get(Command.name == "inline")
    assert inline_alias_command.name == "inline"
    assert inline_alias_command.description == "inline comment"
    assert inline_alias_command.command_type == "ALIAS"
    assert inline_alias_command.code == 'echo "Hello, Inline!"'

    # When: List all categories
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "--cats"])

    # Then: Verify each category shows correct command count
    output = clean_stdout()
    assert re.search(r"code_regex +3", output)
    assert re.search(r"command_name_regex +3", output)
    assert re.search(r"comment_regex +3", output)
    assert re.search(r"path_regex +3", output)
    assert re.search(rf"{UNCATEGORIZED_NAME} +4", output)


def test_index_with_rebuild(mock_files, mock_config, clean_stdout, debug) -> None:
    """Verify that rebuild flag resets hidden state of all commands."""
    # Given: Configure test environment and index initial commands
    settings.update(mock_config(file_globs=[f"{mock_files}/**/*.sh"]))
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["index"])

    # Then: Verify initial database state
    assert File.select().count() == 3
    assert Category.select().count() == 1
    assert Command.select().count() == 9
    assert Command.select().where(Command.hidden == False).count() == 9
    assert Command.select().where(Command.hidden == True).count() == 0
    assert Command.select().where(Command.has_custom_description == False).count() == 9
    assert Command.select().where(Command.has_custom_description == True).count() == 0

    # When: Hide a command and re-index without rebuild
    c1 = Command.get(1)
    c1.hidden = True
    c1.save()

    c2 = Command.get(2)
    c2.has_custom_description = True
    c2.description = "Custom description"
    c2.save()

    c3 = Command.get(3)
    c3.has_custom_description = True
    c3.description = "Custom description"
    c3.hidden = True
    c3.save()

    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["index"])

    # Then: Verify hidden command persists
    assert Command.select().where(Command.hidden == False).count() == 7
    assert Command.select().where(Command.hidden == True).count() == 2
    assert Command.select().where(Command.has_custom_description == False).count() == 7
    assert Command.select().where(Command.has_custom_description == True).count() == 2

    # When: Re-index with rebuild flag
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["index", "--rebuild"])

    # Then: Verify rebuild resets all commands to visible
    assert Command.select().where(Command.hidden == False).count() == 9
    assert Command.select().where(Command.hidden == True).count() == 0
    assert Command.select().where(Command.has_custom_description == True).count() == 0

    clean_stdout()  # Only here to suppress output
