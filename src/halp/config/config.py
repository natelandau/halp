"""Instantiate Configuration class and set default values."""

import shutil
import sys
from pathlib import Path
from typing import Any, Optional, TypeVar

import tomllib
import typer
from loguru import logger
from rich import print as rprint

from halp.utils import errors

PATH_CONFIG_DEFAULT = Path(__file__).parent / "default_config.toml"


T = TypeVar("T")


class Config:
    """Representation of a configuration file.

    Attributes:
        config_path (Path | None): The path to the configuration file.
        context (dict[str, Any]): Additional values to add to the configuration.
        config (dict[str, Any]): Loaded configuration data.
    """

    def __init__(
        self, config_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize configuration file.

        Args:
            config_path (Path | None): The path to the configuration file.
            context (dict[str, Any] | None): Additional values to add to the configuration.
        """
        self.config_path = self._resolve_path(config_path)
        self.context = context or {}

        if not self.config_path or not self.config_path.exists():
            self._create_config()

        self.config = self._load_config()

    def __repr__(self) -> str:
        """Return string representation of Config.

        Returns:
            str: The string representation of the Config object.
        """
        return f"{self.config}"

    @staticmethod
    def _resolve_path(config_path: Path | None) -> Path | None:
        """Resolve the given path to an absolute path."""
        if config_path:
            return config_path.expanduser().resolve()
        return None

    def _create_config(self) -> None:
        """Create a configuration file from the default when it does not exist."""
        if self.config_path is None:
            logger.error("No configuration file specified")
            raise typer.Exit(code=1)

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PATH_CONFIG_DEFAULT, self.config_path)
        logger.success(f"Created default configuration file at {self.config_path}")
        rprint(f"{self.config_path} created. Please edit before continuing.")
        sys.exit(1)

    def _load_config(self) -> dict[str, Any]:
        """Load the configuration file."""
        logger.trace(f"Loading configuration from {self.config_path}")
        try:
            with self.config_path.open("rb") as f:
                config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            logger.exception(f"Could not parse '{self.config_path}'")
            raise typer.Exit(code=1) from e

        return {**config, **self.context}

    def validate(self) -> None:
        """Validate the configuration file.

        Ensures that the configuration file is not empty and that the 'categories' section,
        if present, is properly formatted.
        """
        # No empty config files
        if not self.config:
            msg = f"Configuration file is empty\nConfig file: {self.config_path}"
            raise errors.InvalidConfigError(msg)

        # Validate categories
        if (categories := self.config.get("categories")) is not None:
            if not isinstance(categories, dict):
                msg = f"Categories must be a dictionary\nConfig file: {self.config_path}"
                raise errors.InvalidConfigError(msg)

            for category_key, category_value in categories.items():
                if not isinstance(category_value, dict):
                    msg = f"Category '{category_key}' must be a dictionary. Config file: {self.config_path}"
                    raise errors.InvalidConfigError(msg)
                if "category_name" not in category_value:
                    msg = f"Category '{category_key}' is missing a 'category_name' value. Config file: {self.config_path}"
                    raise errors.InvalidConfigError(msg)

    def rebuild(self) -> None:
        """Rebuild the configuration file from the default.

        This method deletes the existing configuration file, if present,
        and then creates a new one from the default configuration.
        """
        try:
            if self.config_path and self.config_path.exists():
                logger.info(f"Deleting existing configuration file: {self.config_path}")
                self.config_path.unlink()
            self._create_config()
            logger.info("Configuration file rebuilt from the default.")
        except (FileNotFoundError, PermissionError) as e:
            logger.exception(f"Failed to rebuild configuration: {e}")
            msg = f"Error rebuilding configuration: {e}"
            raise errors.ConfigRebuildError(msg) from e

    def get(self, key: str, default: Optional[T] = None, pass_none: bool = False) -> Optional[T]:
        """Get a value from the configuration file.

        Args:
            key (str): The name of the config variable.
            default (Optional[T]): The default value if the key is not set. Type is generic.
            pass_none (bool): If True, returns None if the key does not exist; otherwise, returns the default.

        Returns:
            Optional[T]: The value of the config variable, or the default value if not set. Type is generic.
        """
        value = self.config.get(key)

        if value is None:
            if pass_none:
                return None
            logger.trace(f"Config variable '{key}' is not set. Using default value.")
            return default

        # If specific string handling is required, explain the reason here
        # e.g., to remove specific quotes from a configuration value
        if isinstance(value, str):
            # Example of custom string processing (if needed)
            value = value.strip().lstrip('"').rstrip('"')

        return value
