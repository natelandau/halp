# type: ignore
"""Test configuration model."""

import shutil
from pathlib import Path

import pytest
import typer

from halper.config.config import PATH_CONFIG_DEFAULT, Config


def test_validate_1():
    """Test validation a configuration file.

    GIVEN a request to validate a configuration file
    WHEN no path is provided
    THEN raise an exception
    """
    with pytest.raises(typer.Exit):
        Config().validate()


def test_init_config_3(tmp_path):
    """Test initializing a configuration file.

    GIVEN a request to initialize a configuration file
    WHEN a path to the default configuration file is provided
    THEN load the configuration file
    """
    path_to_config = Path(tmp_path / "config.toml")
    shutil.copy(PATH_CONFIG_DEFAULT, path_to_config)
    config = Config(config_path=path_to_config, context={"dry_run": False})
    assert config.config_path == path_to_config
    config.validate()
    assert config.config == {
        "case_sensitive": False,
        "categories": {},
        "command_name_ignore_regex": "",
        "file_exclude_regex": "",
        "file_globs": [],
        "dry_run": False,
    }
    assert config.context == {"dry_run": False}


def test_init_config_4(tmp_path):
    """Test initializing a configuration file.

    GIVEN a request to initialize a configuration file
    WHEN values are provided in the context
    THEN load the configuration file
    """
    path_to_config = Path(tmp_path / "config.toml")
    shutil.copy(PATH_CONFIG_DEFAULT, path_to_config)
    config = Config(config_path=path_to_config, context={"dry_run": True, "force": True})
    assert config.config_path == path_to_config
    config.validate()
    assert config.config == {
        "case_sensitive": False,
        "categories": {},
        "command_name_ignore_regex": "",
        "file_exclude_regex": "",
        "file_globs": [],
        "dry_run": True,
        "force": True,
    }
    assert config.context == {"dry_run": True, "force": True}
