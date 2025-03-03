"""Test the hide and the unhide subcommands."""

import cappa
import pytest

from halper.halp import Halp
from halper.models import Command
from halper.utils import settings


@pytest.fixture(autouse=True)
def mock_initialize_subcommand(mocker, tmp_path):
    """Mock the initialization of the halp config file for testing to allow tests to run without a real config file.

    This fixture automatically runs before each test to create a temporary config file and patch the USER_CONFIG_PATH. This ensures tests have a clean, isolated config environment without affecting the real user config.
    """
    path_to_config = tmp_path / "halp.toml"
    path_to_config.touch()
    mocker.patch("halper.cli.helpers.USER_CONFIG_PATH", path_to_config)


def test_hide_command(mock_config, clean_stdout, populate_db, debug, mocker, tmp_path) -> None:
    """Verify that the hide and unhide CLI commands correctly toggle command visibility."""
    # Given: A command that exists in the database and is visible
    test_command = Command.get(1)
    assert not test_command.hidden

    # When: Hide the command using the CLI hide command
    settings.update(mock_config())
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["hide", "1"])

    # Then: Verify the command is now hidden in the database
    test_command = Command.get(1)
    assert test_command.hidden

    # When: Unhide the command using the CLI unhide command
    settings.update(mock_config())
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["unhide", "1"])

    # Then: Verify the command is visible again in the database
    test_command = Command.get(1)
    assert not test_command.hidden

    # Suppress CLI output to keep test output clean
    clean_stdout()
