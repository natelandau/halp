"""View the current configuration."""

import typer
from rich.syntax import Syntax

from halp.constants import CONFIG
from halp.utils import console


def view_config() -> None:
    """View the current configuration.

    The function exits the application using typer.Exit, ensuring a graceful shutdown.
    """
    if not CONFIG.config_path.exists():
        console.print("No configuration file found.")
        raise typer.Exit(code=1)

    console.print(f"\n[bold]Configuration path:[/bold] '{CONFIG.config_path}'\n")
    config_text = CONFIG.config_path.read_text()
    console.print(Syntax(config_text, "toml", word_wrap=True))
    typer.launch(str(CONFIG.config_path), locate=True)
    raise typer.Exit()
