"""Tests for the halp command."""

import cappa
import pytest

from halper.halp import Halp


@pytest.mark.no_db
def test_halp_help(capsys, debug) -> None:
    """Verify that the help flag displays proper usage information and available subcommands."""
    # Given: A CLI runner instance
    # When: Request help documentation with -h flag
    with pytest.raises(cappa.Exit):
        cappa.invoke(obj=Halp, argv=["-h"])

    # Then: Display usage instructions and subcommands
    output = capsys.readouterr().out
    assert "Usage: halp [-v]" in output
    assert "Subcommands" in output
