"""Instantiate Configuration class and set default values."""

import shutil
from pathlib import Path
from typing import Any, Optional, TypeVar

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore [no-redef]

import typer
from loguru import logger
from rich import print as rprint

from halper.utils import errors

PATH_CONFIG_DEFAULT = Path(__file__).parent / "default_config.toml"


T = TypeVar("T")


class Config:
    """Manage the configuration file operations for an application.

    This class facilitates the loading, validation, and retrieval of configuration data from a specified file, and integrates additional context into the configuration when necessary.

    Attributes:
        config_path (Optional[Path]): The path to the configuration file.
        context (dict[str, Any]): Additional context to merge with the configuration.
        config (dict[str, Any]): The configuration data loaded from the file.
    """

    def __init__(
        self, config_path: Path | None = None, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize the Config instance.

        Determine the configuration file path and store the additional context. If no path is provided, set it to None.

        Args:
            config_path (Optional[Path]): The path to the configuration file.
            context (Optional[dict[str, Any]]): Additional context to integrate into the configuration.
        """
        self.config_path = self._resolve_path(config_path)
        self.context = context or {}

        self.config: dict[str, Any] = {}

    def __repr__(self) -> str:
        """Return the string representation of the Config instance.

        Returns:
            str: The string representation of the configuration data.
        """
        return f"{self.config}"

    @staticmethod
    def _resolve_path(config_path: Path | None) -> Path | None:
        """Resolve the given file path to an absolute path.

        If a path is provided, expand the user (~) and resolve it to an absolute path. Return None if no path is provided.

        Args:
            config_path (Optional[Path]): The path to be resolved.

        Returns:
            Optional[Path]: The resolved absolute path, or None if no path was provided.
        """
        if config_path:
            return config_path.expanduser().resolve()

        return None

    def _create_empty_config(self) -> None:
        """Create a default configuration file if it does not exist.

        Check if the configuration path is set. If not, log an error and exit. If the path is set, create the required directories and copy the default configuration file to this location. Then exit the application.
        """
        if self.config_path is None:
            logger.error("No configuration file specified")
            raise typer.Exit(code=1)

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PATH_CONFIG_DEFAULT, self.config_path)

        msg = (
            "[bold]halp requires a configuration file to run.[/bold]",
            "Empty configuration created, edit before continuing",
        )

        rprint("\n".join(msg))
        self.edit_config(exit_code=1)

    def _load_config(self) -> dict[str, Any]:
        """Load the configuration data from the file.

        Open and read the configuration file, parsing its contents. Log any exceptions and exit if an error occurs.

        Returns:
            dict[str, Any]: The loaded configuration data.
        """
        logger.trace(f"Loading configuration from {self.config_path}")
        try:
            with self.config_path.open("rb") as f:
                config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            logger.exception(f"Could not parse '{self.config_path}'")
            raise typer.Exit(code=1) from e

        return {**config, **self.context}

    def edit_config(self, exit_code: int = 0) -> None:
        """Attempt to open the configuration file for the user to edit.

        Args:
            exit_code (int): The exit code to use when exiting the application.

        Raises:
            typer.Exit: Raised after attempting to open the configuration file.
        """
        if not self.config_path.exists():
            self._create_empty_config()

        msg = f"""
Config file: '{self.config_path}'
[dim]Attempting to open file...[/dim]
    """
        rprint(msg)
        typer.launch(str(self.config_path), locate=True)
        raise typer.Exit(exit_code)

    def validate(self) -> bool:
        """Validate and load the configuration file.

        Ensure the file exists and is not empty. Validate the 'categories' section, if present. Load the configuration data into self.config.

        Returns:
            bool: True if the configuration file is valid, False otherwise.

        Raises:
            InvalidConfigError: Raised if the configuration file is empty.
            InvalidConfigError: Raised if the 'categories' section is not a dictionary.
            InvalidConfigError: Raised if a category is not a dictionary.
            InvalidConfigError: Raised if a category is missing a 'category_name' value.
        """
        if not self.config_path or not self.config_path.exists():
            self._create_empty_config()

        self.config = self._load_config()

        with PATH_CONFIG_DEFAULT.open("rb") as f:
            default_config = tomllib.load(f)

        if self.config == default_config:
            rprint(
                "Configuration file is using default values. Please edit the file before continuing.\nRun [code]halp --edit-config[/code] to open the file."
            )
            raise typer.Exit(code=1)

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

        return True

    def get(self, key: str, default: Optional[T] = None, pass_none: bool = False) -> Optional[T]:
        """Retrieve a configuration value by key.

        Fetch the value associated with the given key. Return None or a default value if the key is not found.

        Args:
            key (str): The key of the configuration item to retrieve.
            default (Optional[T]): The default value to return if the key is not found.
            pass_none (bool): If True, return None when the key is not found; otherwise, return the default value.

        Returns:
            Optional[T]: The configuration value or default.
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
