"""Views for commands."""

from halper.models import Command
from halper.utils import console, pp


def command_detail_view(commands: list[Command], input_string: str, *, found_in_tldr: bool) -> None:
    """Display detailed command information in a formatted table view.

    Format and print command details to the console, with options for full output and tldr integration. When multiple commands match, display a header showing the match count and separate each command with a horizontal rule. This function is useful for presenting command documentation in an organized, readable format.

    Args:
        commands (list[Command]): List of Command objects containing details to display
        input_string (str): Original search string used to find these commands, shown in header
        full_output (bool): Display comprehensive command details when True, abbreviated when False
        found_in_tldr (bool): Indicate if command documentation exists in tldr pages

    Note:
        Command IDs are shown when either full_output is True or multiple commands are displayed.
        Uses rich console formatting for styled terminal output.
    """
    print_separator = len(commands) > 1

    if print_separator:
        pp.info(f"Found {len(commands)} commands matching: [code]{input_string}[/code]")

    for command in commands:
        if print_separator:
            console.rule()

        console.print(command.table(found_in_tldr=found_in_tldr))

    if print_separator:
        console.rule()
