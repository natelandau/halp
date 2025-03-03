"""Representation of user defined categories built from the configuration file."""

from dataclasses import dataclass


@dataclass
class ConfigurationCategory:
    """User defined category configuration."""

    name: str = ""
    code_regex: str = ""
    comment_regex: str = ""
    description: str = ""
    command_name_regex: str = ""
    path_regex: str = ""
