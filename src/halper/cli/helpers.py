"""Helpers for CLI subcommands."""

import cappa

from halper.constants import USER_CONFIG_PATH, VERSION, PrintLevel
from halper.halp import (
    ConfigCommand,
    Halp,
    HideCommand,
    IndexCommand,
    ListCommand,
    SearchCommand,
    UnhideCommand,
)
from halper.models import Command
from halper.utils import (
    check_python_version,
    db_tables_have_data,
    init_database,
    pp,
    settings,
    validate_settings,
)


def initialize_subcommand(
    halp: Halp,
    subcommand: IndexCommand
    | SearchCommand
    | ListCommand
    | ConfigCommand
    | UnhideCommand
    | HideCommand,
    *,
    require_db_content: bool = False,
    require_config: bool = True,
    no_db: bool = False,
) -> None:
    """Initialize and validate a CLI subcommand environment.

    Set up logging, validate settings and Python version, initialize the database, and optionally verify database content. This function handles common setup tasks required before executing any CLI subcommand.

    Args:
        halp (Halp): The main Halp application instance containing global settings and verbosity level
        subcommand (cappa.Command): The subcommand instance being initialized
        require_db_content (bool, optional): If True, verify that the database contains indexed commands. Defaults to False.
        require_config (bool, optional): If True, verify that the configuration file exists. Defaults to True.
        no_db (bool, optional): If True, do not initialize the database. Defaults to False.

    Raises:
        cappa.Exit: Exit with code 1 if Python version is < 3.10 or if database content is required but missing

    Note:
        When require_db_content is True, this function will check if commands have been indexed and provide guidance to run the index command if needed. This is useful for subcommands that depend on having commands in the database to function.
    """
    pp.configure(
        debug=halp.verbosity in {PrintLevel.DEBUG, PrintLevel.TRACE},
        trace=halp.verbosity == PrintLevel.TRACE,
    )
    validate_settings()

    if not check_python_version():
        pp.error("Python version must be >= 3.10")
        raise cappa.Exit(code=1)

    if require_config and not USER_CONFIG_PATH.exists():
        pp.error("No configuration file found, create one with [code]halp config[/code]")
        raise cappa.Exit(code=1)

    if halp.verbosity == PrintLevel.TRACE:
        pp.trace(f"Halper v{VERSION} Trace")
        pp.trace(f"Propagated Args: {halp.__dict__}")
        pp.trace(f"Subcommand Args: {subcommand.__dict__}")
        pp.trace(f"Settings: {settings.to_dict()}")

    if not no_db:
        init_database(VERSION)

    if require_db_content and not db_tables_have_data([Command]):
        pp.warning("No indexed commands found in database.")
        pp.info(
            "Make sure your configuration file is up to date and run [code]halp --index[/code] to index your commands."
        )
        raise cappa.Exit(code=1)
