# type: ignore
"""Test halp CLI."""

import re

from typer.testing import CliRunner

from halp.cli import app
from tests.helpers import strip_ansi

runner = CliRunner()


def test_version():
    """Test printing version and then exiting."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert re.match(r"halp version: \d+\.\d+\.\d+", strip_ansi(result.output))
