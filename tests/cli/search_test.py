"""Tests for the search subcommand."""

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


@pytest.fixture(autouse=True)
def mock_third_party_calls(mocker):
    """Mock the calls to mankier and tldr so we don't make calls to the internet or installed binaries during testing."""
    mocker.patch("halper.cli.search.get_mankier_table", return_value="Mocked mankier table")
    mocker.patch("halper.cli.search.get_tldr_command", return_value=False)


def test_mankier_table(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that the mankier table is displayed on commands with a space."""
    # Given: Default settings
    settings.update(mock_config())

    # When: Search for a specific command
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["search", "two parts"])

    # Then: Display the mankier table
    output = clean_stdout()
    assert "Mocked mankier table" in output


def test_list_single_command(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that searching for an existing command displays its details."""
    # Given:  Default settings
    settings.update(mock_config())

    # When: Search for a specific command
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["search", "func2"])

    # Then: Display the command details with proper formatting
    output = clean_stdout()
    assert re.search(r"Command: +func2", output)


def test_non_existent_command(mock_config, clean_stdout, populate_db, debug, caplog) -> None:
    """Verify that searching for a non-existent command displays a clear error message."""
    # Given: Default settings
    settings.update(mock_config())

    # When: Search for a command that doesn't exist
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["search", "nonexistent"])

    # Then: Display "not found" message
    output = clean_stdout()
    # debug(output)
    assert "No command found matching: nonexistent" in output


def test_regex_search(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that regex pattern matching finds and displays multiple matching commands."""
    # Given: Configure default settings for test environment
    settings.update(mock_config())

    # When: Search using regex pattern that matches multiple function names
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["search", "--regex", r"fu\w+"])

    # Then: Verify output contains details for all matched commands
    output = clean_stdout()
    # debug(output)
    assert re.search(r"Command: +func2", output)
    assert re.search(r"Command: +func1", output)


def test_code_search(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that code search finds and displays matching commands."""
    # Given: Configure default settings for test environment
    settings.update(mock_config())

    # When: Search using code search
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["search", "-c", r"#this"])

    # Then: Verify output contains details for all matched commands
    output = clean_stdout()
    # debug(output)
    assert not re.search(r"Command: +alias1", output)
    assert re.search(r"Command: +alias2", output)
    assert re.search(r"Command: +alias3", output)
    assert not re.search(r"Command: +alias4", output)


def test_hidden_command(mock_config, clean_stdout, populate_db, debug) -> None:
    """Verify that code search with show_hidden flag only displays hidden commands."""
    # Given: Set up test database with mix of hidden and visible commands
    settings.update(mock_config())

    # When: Search code with show_hidden flag enabled
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["search", "-c", "-x", r"#this"])

    # Then: Only hidden commands matching the pattern should appear
    output = clean_stdout()
    # debug(output)
    assert not re.search(r"Command: +alias1", output)
    assert not re.search(r"Command: +alias2", output)
    assert not re.search(r"Command: +alias3", output)
    assert re.search(r"Command: +alias4", output)
