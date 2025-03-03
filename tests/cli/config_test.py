"""Test the config subcommand."""

import cappa
import pytest

from halper.constants import DEFAULT_CONFIG_PATH
from halper.halp import Halp
from halper.utils import settings


@pytest.mark.no_db
def test_new_default_config(mock_config, clean_stdout, debug, tmp_path, mocker) -> None:
    """Verify that config command creates a new default configuration file in non-interactive mode."""
    # Given: Configure a clean temporary directory for the config file
    path_to_config = tmp_path / "halp.toml"
    mocker.patch("halper.cli.config.USER_CONFIG_PATH", path_to_config)
    # Ensure starting with no existing config
    assert path_to_config.exists() is False
    settings.update(mock_config())

    # When: Run config command without --interactive flag
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["config"])

    # Then: Verify config file matches default template
    output = clean_stdout()
    debug(output, "output")

    assert "configuration created" in output
    assert path_to_config.exists() is True
    # Config should be exact copy of default template
    assert path_to_config.read_text() == DEFAULT_CONFIG_PATH.read_text()


@pytest.mark.no_db
def test_overwrite_existing_config(mock_config, clean_stdout, debug, tmp_path, mocker) -> None:
    """Verify that config command overwrites existing configuration file when user confirms."""
    # Given: An existing config file and user confirmation to overwrite
    path_to_config = tmp_path / "halp.toml"
    mocker.patch("halper.cli.config.USER_CONFIG_PATH", path_to_config)
    mocker.patch("halper.cli.config.Confirm.ask", return_value=True)
    path_to_config.touch()
    assert path_to_config.exists() is True
    settings.update(mock_config())

    # When: Run config command in non-interactive mode
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["config"])

    # Then: Verify existing config is replaced with default template
    output = clean_stdout()
    assert "configuration created" in output
    assert path_to_config.exists() is True
    assert path_to_config.read_text() == DEFAULT_CONFIG_PATH.read_text()


def test_overwrite_existing_config_false(
    mock_config, clean_stdout, debug, tmp_path, mocker
) -> None:
    """Verify that config command preserves existing config file when user declines overwrite."""
    # Given: Set up existing config file and mock user declining overwrite
    path_to_config = tmp_path / "halp.toml"
    mocker.patch("halper.cli.config.USER_CONFIG_PATH", path_to_config)
    mocker.patch("halper.cli.config.Confirm.ask", return_value=False)
    path_to_config.touch()
    assert path_to_config.exists() is True
    settings.update(mock_config())

    # When: Run config command which prompts for overwrite
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["config"])

    # Then: Verify original config is preserved and command exits gracefully
    output = clean_stdout()
    assert "Exiting" in output
    assert path_to_config.exists() is True
    assert path_to_config.read_text() != DEFAULT_CONFIG_PATH.read_text()


@pytest.mark.no_db
def test_new_default_interactive(mock_config, clean_stdout, debug, tmp_path, mocker) -> None:
    """Verify that config command creates a new default configuration file in non-interactive mode."""
    # Given: Configure a clean temporary directory for the config file
    path_to_config = tmp_path / "halp.toml"
    mocker.patch("halper.cli.config.USER_CONFIG_PATH", path_to_config)

    # First prompt for the file glob
    path_to_dotfile = tmp_path / "dotfiles.sh"
    path_to_dotfile.touch()
    mocker.patch(
        "halper.cli.config.Prompt.ask",
        side_effect=[str(path_to_dotfile), "exclude_regex", "command_ignore_regex", "best"],
    )

    # Final saving of the config
    mocker.patch("halper.cli.config.Confirm.ask", return_value=True)

    # Ensure starting with no existing config
    assert path_to_config.exists() is False
    settings.update(mock_config())

    # When: Run config command without --interactive flag
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["config", "--interactive"])

    # Then: Verify config file matches default template
    output = clean_stdout()

    # debug(output)

    assert "Config created successfully" in output

    lines_to_check = [
        "dotfiles.sh']",
        "file_exclude_regex = 'exclude_regex'",
        "command_name_ignore_regex = 'command_ignore_regex'",
        'comment_placement = "best"',
    ]
    file_contents = path_to_config.read_text()
    for line in lines_to_check:
        assert line in file_contents

    # debug(path_to_config.read_text(), "config_file")
