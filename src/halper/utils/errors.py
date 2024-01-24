"""Custom errors for Halp."""


class MankierCommandNotFoundError(Exception):
    """Raised when a command is not found on mankier.com."""

    def __init__(
        self,
        msg: str | None = None,
        e: Exception | None = None,
        *args: str | int,
        **kwargs: int | str | bool,
    ):
        formatted_msg = (
            f"Command not found on mankier.com: {msg}"
            if msg
            else "Command not found on mankier.com"
        )
        if e:
            formatted_msg += f"\nRaised from: {e.__class__.__name__}: {e}"
        super().__init__(formatted_msg, *args, **kwargs)


class InvalidConfigError(Exception):
    """Raised when the configuration file is malformed."""

    def __init__(
        self,
        msg: str | None = None,
        e: Exception | None = None,
        *args: str | int,
        **kwargs: int | str | bool,
    ):
        formatted_msg = (
            f"The configuration file is malformed: {msg}"
            if msg
            else "The configuration file is malformed."
        )
        if e:
            formatted_msg += f"\nRaised from: {e.__class__.__name__}: {e}"
        super().__init__(formatted_msg, *args, **kwargs)


class ConfigRebuildError(Exception):
    """Raised when the configuration file cannot be rebuilt."""

    def __init__(
        self,
        msg: str | None = None,
        e: Exception | None = None,
        *args: str | int,
        **kwargs: int | str | bool,
    ):
        formatted_msg = (
            f"The configuration cannot be rebuilt: {msg}"
            if msg
            else "The configuration cannot be rebuilt."
        )
        if e:
            formatted_msg += f"\nRaised from: {e.__class__.__name__}: {e}"
        super().__init__(formatted_msg, *args, **kwargs)


class NoFilesFoundError(Exception):
    """Raised when no files are found to parse."""

    def __init__(
        self,
        msg: str | None = None,
        e: Exception | None = None,
        *args: str | int,
        **kwargs: int | str | bool,
    ):
        formatted_msg = (
            f"No files are found to parse: {msg}" if msg else "No files are found to parse."
        )
        if e:
            formatted_msg += f"\nRaised from: {e.__class__.__name__}: {e}"
        super().__init__(formatted_msg, *args, **kwargs)


class AppDirectoryError(Exception):
    """Raised when the app directory is not configured correctly."""

    def __init__(
        self,
        msg: str | None = None,
        e: Exception | None = None,
        *args: str | int,
        **kwargs: int | str | bool,
    ):
        formatted_msg = (
            f"The app directory is not configured correctly: {msg}"
            if msg
            else "The app directory is not configured correctly"
        )
        if e:
            formatted_msg += f"\nRaised from: {e.__class__.__name__}: {e}"
        super().__init__(formatted_msg, *args, **kwargs)
