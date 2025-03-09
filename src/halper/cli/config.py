"""Config subcommand."""

import re
import shutil
from pathlib import Path

import cappa
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from halper.constants import DEFAULT_CONFIG_PATH, USER_CONFIG_PATH
from halper.halp import ConfigCommand, Halp
from halper.utils import console, pp

from .helpers import initialize_subcommand


def get_file_glob() -> str:
    """Prompt user for a file glob pattern and validate it exists.

    Repeatedly prompts the user to enter a file glob pattern until a valid one is provided. The function validates that the base path exists before accepting the input.

    Returns:
        str: A validated file glob pattern with expanded user path. For example:
            '/home/user/.config/**/*.sh' or '/home/user/dotfiles/bashrc'

    Note:
        This function is used during config setup to specify which files should be indexed for commands.
        It handles both direct file paths and glob patterns with wildcards.
    """
    glob_prompt = "Path or file glob for your dotfiles"
    while True:
        user_file_glob = Prompt.ask(glob_prompt)
        if not user_file_glob:
            pp.error("Please enter a path or file glob for your dotfiles.")
            continue

        split_path = re.split(r"(\*)", user_file_glob)
        add_slash = split_path[0].endswith("/")
        path_to_check = Path(split_path[0]).expanduser().resolve()

        if not path_to_check.exists():
            pp.error(f"{path_to_check} does not exist. Please enter a valid path or glob.")
            continue

        return f"{path_to_check}{'/' if add_slash else ''}{''.join(split_path[1:])}"


def display_section_panel(title: str, content: str, width: int = 100) -> None:
    """Display a rich panel containing markdown formatted content.

    Create and display a panel with a title and markdown content using Rich's Panel and Markdown components.

    Args:
        title (str): The title text to display at the top of the panel
        content (str): The markdown formatted content to display inside the panel
        width (int, optional): The width of the panel in characters. Defaults to 100.

    Note:
        This function is used to display sections of help text and prompts during the interactive
        configuration process. The markdown content will be rendered with proper formatting.
    """
    panel = Panel(Markdown(content), width=width, title=title)
    console.print("\n", panel)


def get_config_input() -> tuple[list[str], str, str, str]:
    """Get user input to configure halp settings interactively.

    Prompts the user for configuration values through a series of interactive prompts with
    explanatory panels. Collects settings for file locations, exclusion patterns, and comment
    parsing preferences.

    Returns:
        tuple[list[str], str, str, str]: A tuple containing:
            - file_globs: List of file glob patterns pointing to files to index
            - file_exclude_regex: Regex pattern for excluding files from indexing
            - command_name_ignore_regex: Regex pattern for excluding specific commands
            - comment_placement: How to parse command descriptions ("best", "above", or "inline")

    Note:
        Use this function when setting up halp's configuration for the first time or when
        updating configuration interactively. The function provides detailed help text and
        validation for each setting to ensure valid configuration.
    """
    # File glob section
    display_section_panel(
        "Location of dotfiles",
        """
**First, we need to tell halp where to find your the file(s) containing your dotfiles which will be indexed.**

You can use globs to match files. For example, `~/.config/dotfiles/**/*.sh` will match all `.sh` files in the `~/.config/dotfiles` directory and all subdirectories.
        """,
    )
    file_globs = [get_file_glob()]

    # Exclude files section
    display_section_panel(
        "Exclude files",
        "[bold]If you added a glob pattern, you can add a regex of files to exclude from the indexer.[/bold]\n[dim]Leave blank if not needed.[/dim]",
    )
    file_exclude_regex = Prompt.ask("Regex of files to exclude")

    # Exclude commands section
    display_section_panel(
        "Exclude commands",
        "[bold]If there are specific commands within your indexed files that you want to exclude, write a regex to exclude them here.[/bold]\n[dim]Leave blank if not needed.[/dim]",
    )
    command_name_ignore_regex = Prompt.ask("Regex of commands to exclude")

    # Comment placement section
    display_section_panel(
        "Comment placement",
        """
**Halp will try it's best to find comments associated with your commands and use them as descriptions.**

- **BEST**: Halp will try to find the best comment placement for your commands.
- **ABOVE**: Halp will find comments above your commands.
  ```shell
  # Description
  alias ll='ls -la'
  ```
- **INLINE**: Halp will find comments inline with your commands.
  ```shell
  alias ll='ls -la' # Description
  ```
""",
    )
    comment_placement = Prompt.ask(
        "Comment placement", choices=["best", "above", "inline"], default="best"
    )

    return file_globs, file_exclude_regex, command_name_ignore_regex, comment_placement


def update_config_file(
    file_globs: list[str],
    file_exclude_regex: str,
    command_name_ignore_regex: str,
    comment_placement: str,
) -> None:
    """Update configuration file with new user-provided values using regex substitution.

    Replace existing configuration values in the TOML file with new values provided by the user. Uses regex patterns to find and replace specific configuration keys while preserving the file structure.

    Args:
        file_globs (list[str]): List of file glob patterns pointing to files that should be indexed
        file_exclude_regex (str): Regex pattern for excluding files from being indexed
        command_name_ignore_regex (str): Regex pattern for excluding specific commands from being indexed
        comment_placement (str): How to parse command descriptions ("best", "above", or "inline")

    Note:
        This function modifies the USER_CONFIG_PATH file in place. The regex patterns are case-insensitive to handle variations in the TOML file format. Use this function after collecting new configuration values to persist them to disk.
    """
    text = USER_CONFIG_PATH.read_text()
    text = re.sub(r"file_globs += +\[.*\]", f"file_globs = {file_globs}", text, flags=re.IGNORECASE)
    text = re.sub(
        r"file_exclude_regex += +''",
        f"file_exclude_regex = '{file_exclude_regex}'",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"command_name_ignore_regex += +''",
        f"command_name_ignore_regex = '{command_name_ignore_regex}'",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'comment_placement += +"BEST"',
        f'comment_placement = "{comment_placement}"',
        text,
        flags=re.IGNORECASE,
    )
    USER_CONFIG_PATH.write_text(text)


def config_command(halp: Halp, cmd: ConfigCommand) -> None:
    """Create or update the halp configuration file interactively or non-interactively.

    Guides users through creating a new configuration file by prompting for file locations to index, exclusion patterns, and comment parsing preferences. Can also create an empty config file in non-interactive mode.

    Args:
        halp (Halp): The main application instance containing global settings
        cmd (ConfigCommand): The config subcommand instance with interactive flag

    Raises:
        cappa.Exit: Exit with code 0 if user cancels or after successful config creation

    Note:
        Use this command to set up halp for first time use or to reconfigure settings. The interactive mode provides helpful explanations and validation, while non-interactive mode creates an empty config file that can be manually edited.
    """
    initialize_subcommand(
        halp=halp, subcommand=cmd, require_db_content=False, require_config=False, no_db=True
    )

    if USER_CONFIG_PATH.exists() and not Confirm.ask(
        f"Configuration file already exists: [code]{USER_CONFIG_PATH}[/code]\nOverwrite?"
    ):
        pp.info("Exiting...")
        raise cappa.Exit(code=0)

    # Handle non-interactive mode
    if not cmd.interactive:
        USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(DEFAULT_CONFIG_PATH, USER_CONFIG_PATH)
        pp.info(
            f":rocket: [bold]Empty configuration created[/bold]. Edit before continuing: {USER_CONFIG_PATH}"
        )
        raise cappa.Exit(code=0)

    console.rule("[bold]Create new configuration file[/bold]")
    try:
        # Get all config inputs
        file_globs, file_exclude_regex, command_name_ignore_regex, comment_placement = (
            get_config_input()
        )

        # Display final configuration
        display_section_panel(
            "Completed Configuration",
            f"""
```toml
file_globs = {file_globs}
file_exclude_regex = '{file_exclude_regex}'
command_name_ignore_regex = '{command_name_ignore_regex}'
comment_placement = "{comment_placement}"
```
""",
        )

        if not Confirm.ask("Save configuration?"):
            pp.info("Exiting...")
            raise cappa.Exit(code=0)

        # Create and update config file
        USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(DEFAULT_CONFIG_PATH, USER_CONFIG_PATH)
        update_config_file(
            file_globs, file_exclude_regex, command_name_ignore_regex, comment_placement
        )

        pp.info(f"\n:rocket: [bold]Config created successfully[/bold]: {USER_CONFIG_PATH}")
        raise cappa.Exit(code=0)

    except KeyboardInterrupt as e:
        pp.info("\n[red]Exiting...[/red]")
        raise cappa.Exit(code=0) from e
