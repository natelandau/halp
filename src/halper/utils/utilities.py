"""Utility functions."""

import sys

import sh


def check_python_version() -> bool:
    """Verify that the current Python version meets minimum requirements.

    Check if the running Python interpreter version is >= 3.10. This validation is important for ensuring the application has access to required language features like pattern matching and other 3.10+ functionality.

    Returns:
        bool: True if Python version is >= 3.10, False otherwise.
    """
    return sys.version_info >= (3, 10)


def strip_last_two_lines(multiline_string: str) -> str:
    r"""Remove the last two lines from a multiline string.

    Split a multiline string into lines, remove the last two lines, and rejoin the remaining lines. This is particularly useful when processing man pages or command output that contains unwanted footer information or trailing metadata.

    Args:
        multiline_string (str): The input string containing multiple lines of text.

    Returns:
        str: The processed string with the last two lines removed, joined with newlines.

    Example:
        >>> text = "Line 1\nLine 2\nFooter\nMetadata"
        >>> strip_last_two_lines(text)
        'Line 1\nLine 2'
    """
    # Split the string into lines
    lines = multiline_string.splitlines()

    # Remove the last line and rejoin the remaining lines
    return "\n".join(lines[:-2])


def get_tldr_command() -> sh.Command | None:  # pragma: no cover
    """Get a configured 'tldr' command for displaying command documentation.

    Attempt to locate and configure the tldr command-line tool for displaying simplified man pages. The returned command is pre-configured with the quiet flag (-q) to reduce noise in the output. This function enables integration with the tldr documentation system as a fallback when local command documentation is not available.

    Returns:
        sh.Command | None: A configured sh.Command instance for the tldr command if available on the system, None if tldr is not installed or cannot be found.
    """
    try:
        tldr_path = sh.which("tldr").strip()
        return sh.Command(tldr_path).bake("-q")
    except sh.ErrorReturnCode:
        return None
    except sh.CommandNotFound:
        return None
