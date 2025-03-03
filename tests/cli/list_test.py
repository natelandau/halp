"""Test the list subcommand."""

import re

import cappa
import pytest

from halper.halp import Halp
from halper.utils import settings


@pytest.fixture(autouse=True)
def mock_initialize_subcommand(mocker, tmp_path):
    """Mock the initialization of the halp config file for testing to allow tests to run without a real config file.

    This fixture automatically runs before each test to create a temporary config file and patch the USER_CONFIG_PATH. This ensures tests have a clean, isolated config environment without affecting the real user config.
    """
    path_to_config = tmp_path / "halp.toml"
    path_to_config.touch()
    mocker.patch("halper.cli.helpers.USER_CONFIG_PATH", path_to_config)


def test_list_default(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command displays all non-hidden commands with default formatting."""
    # Given: Configure test environment with populated database
    settings.update(mock_config())

    # When: Execute list command without flags
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list"])

    # Then: Verify output shows expected non-hidden commands with default columns
    output = clean_stdout()
    assert "7 commands" in output
    assert "alias2 description" in output
    assert "Category" in output
    assert "Type" not in output
    assert "File" not in output
    assert "ID" not in output
    assert "Alias" not in output


def test_list_short(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command displays minimal output in short format."""
    # Given: Configure test environment with populated database
    settings.update(mock_config())

    # When: Execute list command with short flag
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "--short"])

    # Then: Verify output shows only command names without additional details
    output = clean_stdout()
    assert "7 commands" in output
    assert "alias2 description" not in output
    assert "Category" not in output
    assert "Type" not in output
    assert "File" not in output
    assert "ID" not in output
    assert "Alias" not in output


def test_list_default_full(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command displays all available columns in full format."""
    # Given: Configure test environment with populated database
    settings.update(mock_config())

    # When: Execute list command with full flag
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "--full"])

    # Then: Verify output includes all possible columns
    output = clean_stdout()
    assert "7 commands" in output
    assert "alias2 description" in output
    assert "Category" in output
    assert "Type" in output
    assert "File" in output
    assert "ID" in output
    assert "Alias" in output


def test_list_hidden_commands(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command displays only hidden commands when requested."""
    # Given: Configure test environment with populated database containing hidden commands
    settings.update(mock_config())

    # When: Execute list command with hidden flag
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "--hidden"])

    # Then: Verify output shows only hidden commands
    output = clean_stdout()
    assert "1 command" in output
    assert "alias4" in output


def test_list_no_commands(mock_config, clean_stdout, debug) -> None:
    """Verify that list command handles empty database gracefully."""
    # Given: Configure test environment with empty database
    settings.update(mock_config())

    # When: Execute list command
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list"])

    # Then: Verify appropriate message is displayed
    output = clean_stdout()
    assert "No indexed commands found in database" in output


def test_list_category_not_found(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command handles non-existent category searches appropriately."""
    # Given: Configure test environment with populated database
    settings.update(mock_config())

    # When: Search for non-existent category
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "category1"])

    # Then: Verify error message is displayed
    output = clean_stdout()
    assert "No category found matching: 'category1'" in output


def test_list_single_category(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command filters commands by exact category match."""
    # Given: Configure test environment with populated database
    settings.update(mock_config())

    # When: Search for specific category
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "cat1"])

    # Then: Verify output shows only commands from specified category
    output = clean_stdout()
    assert re.search(r"Command +Description", output)
    assert "alias1" in output
    assert "alias1 description" in output
    assert "3 commands" in output
    assert "cat1" in output
    assert "cat2" not in output


def test_list_single_category_short(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command displays commands in short format when filtering by exact category match."""
    # Given: Configure test environment with populated database
    settings.update(mock_config())

    # When: List commands from category 'cat1' in short format
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "--short", "cat1"])

    # Then: Verify output shows only command names without descriptions
    output = clean_stdout()
    assert not re.search(r"Command +Description", output)  # No header row in short format
    assert "alias1" in output  # Command name is shown
    assert "alias1 description" not in output  # Description is omitted
    assert "3 cat1 commands" in output  # Shows count and category
    assert "cat2" not in output  # Other categories are filtered out


def test_list_multiple_category(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command filters commands by partial category match."""
    # Given: Configure test environment with populated database
    settings.update(mock_config())

    # When: Search with partial category name
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "cat"])

    # Then: Verify output shows commands from all matching categories
    output = clean_stdout()
    assert re.search(r"Command +Description", output)
    assert "alias1" in output
    assert "alias3" in output
    assert "3 commands" in output
    assert "4 commands" in output
    assert "cat1" in output
    assert "cat2" in output


def test_list_categories(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that list command displays category summary statistics."""
    # Given: Configure test environment with populated database
    settings.update(mock_config())

    # When: Request category listing
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["list", "--cats"])

    # Then: Verify output shows categories with command counts
    output = clean_stdout()
    assert re.search(r"Category +# Commands", output)
    assert re.search(r"cat1 +3", output)
    assert re.search(r"cat2 +4", output)
