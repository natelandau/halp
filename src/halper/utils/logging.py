"""Logging utilities for Halp."""  # noqa: A005

import logging
import sys
from enum import Enum
from pathlib import Path

from loguru import logger


class LogLevel(Enum):
    """Log levels for halp."""

    INFO = 0
    DEBUG = 1
    TRACE = 2
    WARNING = 3
    ERROR = 4


def instantiate_logger(
    verbosity: int, log_file: Path, log_to_file: bool
) -> None:  # pragma: no cover
    """Instantiate the Loguru logger for Halp.

    Configure the logger with the specified verbosity level, log file path,
    and whether to log to a file.

    Args:
        verbosity (int): The verbosity level of the logger. Valid values are:
            - 0: Only log messages with severity level INFO and above will be displayed.
            - 1: Only log messages with severity level DEBUG and above will be displayed.
            - 2: Only log messages with severity level TRACE and above will be displayed.
            > 2: Include debug from installed libraries
        log_file (Path): The path to the log file where the log messages will be written.
        log_to_file (bool): Whether to log the messages to the file specified by `log_file`.
    """
    level = verbosity if verbosity < 3 else 2  # noqa: PLR2004

    logger.remove()
    logger.add(
        sys.stdout,
        level=LogLevel(level).name,
        colorize=True,
        format="<level>{level: <8}</level> | <level>{message}</level> <fg #c5c5c5>({name}:{function}:{line})</fg #c5c5c5>"
        if LogLevel(verbosity) in {LogLevel.DEBUG, LogLevel.TRACE}
        else "<level>{level: <8}</level> | <level>{message}</level>",
    )
    if log_to_file:
        logger.add(
            log_file,
            level=LogLevel(level).name,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message} ({name})",
            rotation="50 MB",
            retention=2,
            compression="zip",
        )

    if verbosity > 2:  # noqa: PLR2004
        # Intercept standard sh logs and redirect to Loguru
        logging.getLogger("peewee").setLevel(level="DEBUG")
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


class InterceptHandler(logging.Handler):  # pragma: no cover
    """Intercepts standard logging and redirects to Loguru.

    This class is a logging handler that intercepts standard logging messages and redirects them to Loguru, a third-party logging library. When a logging message is emitted, this handler determines the corresponding Loguru level for the message and logs it using the Loguru logger.

    Methods:
        emit: Intercepts standard logging and redirects to Loguru.

    Examples:
    To use the InterceptHandler with the Python logging module:
    ```
    import logging
    from logging import StreamHandler

    from loguru import logger

    # Create a new InterceptHandler and add it to the Python logging module.
    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[StreamHandler(), intercept_handler], level=logging.INFO)

    # Log a message using the Python logging module.
    logging.info("This message will be intercepted by the InterceptHandler and logged using Loguru.")
    ```
    """

    @staticmethod
    def emit(record: logging.LogRecord) -> None:
        """Intercepts standard logging and redirects to Loguru.

        This method is called by the Python logging module when a logging message is emitted. It intercepts the message and redirects it to Loguru, a third-party logging library. The method determines the corresponding Loguru level for the message and logs it using the Loguru logger.

        Args:
            record: A logging.LogRecord object representing the logging message.
        """
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore [assignment]

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6  # noqa: SLF001
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
