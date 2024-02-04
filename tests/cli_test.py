# type: ignore
"""Test halp CLI."""

import re
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from halper.cli import app
from halper.models import Category, Command, CommandCategory, Database, File
from tests.helpers import strip_ansi

runner = CliRunner()


@pytest.fixture(autouse=True)
def _bypass_functions(mocker):
    """Bypass functionality which requires a production environment."""
    mocker.patch.object(Database, "instantiate", MagicMock())
    mocker.patch("halper.cli.validate_config", return_value=None)


@pytest.mark.usefixtures("mock_db")
class TestCLI:
    """Test the cli."""

    @staticmethod
    def _clear_test_data():
        """Clear test data from the database."""
        Category.delete().execute()
        File.delete().execute()
        Command.delete().execute()
        CommandCategory.delete().execute()

    def _populate_database(self):
        """Populate the database with data."""
        # First, clear existing data
        self._clear_test_data()

        # Then, create new data
        file = File.create(name="test", path="test")
        cat1 = Category.create(name="cat1")
        cat2 = Category.create(name="cat2")

        alias1 = Command.create(
            name="alias1", code="alias1", description="alias1", command_type="alias", file=file
        )
        CommandCategory.create(command=alias1, category=cat1)

        alias2 = Command.create(
            name="alias2", code="alias2", description="alias2", command_type="alias", file=file
        )
        CommandCategory.create(command=alias2, category=cat1)

        alias3 = Command.create(
            name="alias3", code="alias3", description="alias3", command_type="alias", file=file
        )
        CommandCategory.create(command=alias3, category=cat2)

        func1 = Command.create(
            name="func1", code="func1", description="func1", command_type="function", file=file
        )
        CommandCategory.create(command=func1, category=cat1)

        func2 = Command.create(
            name="func2", code="func2", description="func2", command_type="function", file=file
        )
        CommandCategory.create(command=func2, category=cat2)

        export1 = Command.create(
            name="export1", code="export1", description="export1", command_type="export", file=file
        )
        CommandCategory.create(command=export1, category=cat2)

        export2 = Command.create(
            name="export2", code="export2", description="export2", command_type="export", file=file
        )
        CommandCategory.create(command=export2, category=cat2)

    def test_version(self):
        """Test printing version and then exiting."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert re.match(r"halp version: \d+\.\d+\.\d+", strip_ansi(result.output))

    def test_no_commands_in_index(self, debug, mock_config):
        """Test the main command."""
        # Given an empty database
        self._clear_test_data()

        result = runner.invoke(app, [])
        assert result.exit_code == 1
        assert "No commands found" in strip_ansi(result.output)

    def test_fail_when_no_args(self, debug, mock_config):
        """Test the main command."""
        # Given a populated database
        self._populate_database()

        result = runner.invoke(app, [])
        assert result.exit_code == 1
        assert "No command specified" in strip_ansi(result.output)

    @pytest.mark.parametrize(
        ("repopulate", "args", "expected", "not_expected", "exit_code"),
        [
            pytest.param(
                True,
                ["alias1"],
                """\
                Command:     alias1
                Description: alias1
                Categories:  cat1
                Type:        Alias
                File:        test
                """,
                "Code:        alias1",
                0,
                id="Find one command",
            ),
            pytest.param(
                True,
                ["--full", "alias1"],
                """\
                Command:     alias1
                Description: alias1
                Categories:  cat1
                Type:        Alias
                File:        test
                Code:        alias1
                """,
                "",
                0,
                id="Find one command w/ full output",
            ),
            pytest.param(
                True,
                ["--full", "--category", "cat1"],
                """\
                alias1    Alias      alias1        1    test
                alias2    Alias      alias2        2    test
                func1     Function   func1         4    test
                """,
                "alias3    Alias      alias3        3    test ",
                0,
                id="Find one category",
            ),
            pytest.param(
                True,
                ["--full", "--category", "cat"],
                """\
                alias1    Alias      alias1        1    test
                alias2    Alias      alias2        2    test
                func1     Function   func1         4    test
                alias3    Alias      alias3        3    test
                export2   Export     export2       7    test
                func2     Function   func2         5    test
                """,
                "",
                0,
                id="Find two categories",
            ),
            pytest.param(
                True,
                ["--full", "--category", "not_a_category"],
                """\
                No categories found matching: not_a_category
                """,
                "",
                1,
                id="Find no categories",
            ),
            pytest.param(
                True,
                ["--list"],
                """\
                7 commands
                alias1
                alias2
                alias3
                func1
                func2
                export1
                export2
                """,
                "",
                0,
                id="List command names",
            ),
            pytest.param(
                True,
                ["--list", "--full"],
                """\
                alias1    cat1         Alias      alias1        1    test
                alias2    cat1         Alias      alias2        2    test
                alias3    cat2         Alias      alias3        3    test
                export1   cat2         Export     export1       6    test
                export2   cat2         Export     export2       7    test
                func1     cat1         Function   func1         4    test
                func2     cat2         Function   func2         5    test
                """,
                "",
                0,
                id="List command names w/ full output",
            ),
            pytest.param(
                True,
                ["--list", "--cat"],
                "2 categories",
                "",
                0,
                id="List categories",
            ),
        ],
    )
    def test_core_functionality(
        self, debug, mock_config, repopulate, args, expected, not_expected, exit_code
    ):
        """Test the main command."""
        # Given a populated database
        if repopulate:
            self._populate_database()

        result = runner.invoke(app, args)
        # debug("output", strip_ansi(result.output))

        assert result.exit_code == exit_code

        for line in expected.splitlines():
            assert line.strip() in strip_ansi(result.output)

        for line in not_expected.splitlines():
            assert line.strip() not in strip_ansi(result.output)

    def test_hide_commands(self, debug, mock_config):
        """Test hiding commands."""
        # Given a populated database
        self._populate_database()

        # WHEN hiding commands
        result = runner.invoke(app, ["--hide", "1,3"])
        # debug("output", strip_ansi(result.output))

        # THEN the commands are marked as hidden
        assert result.exit_code == 0
        assert "Command alias1 hidden" in strip_ansi(result.output)
        assert "Command alias3 hidden" in strip_ansi(result.output)

        # WHEN listing commands
        result = runner.invoke(app, ["--list"])
        # debug("output", strip_ansi(result.output))

        # THEN the hidden commands are not listed
        assert result.exit_code == 0
        assert "5 commands" in strip_ansi(result.output)
        assert "alias1" not in strip_ansi(result.output)
        assert "alias3" not in strip_ansi(result.output)

        # WHEN listing hidden commands
        result = runner.invoke(app, ["--list-hidden"])
        # debug("output", strip_ansi(result.output))

        # THEN the hidden commands are listed
        assert result.exit_code == 0
        assert "alias1    cat1         alias1        1" in strip_ansi(result.output)
        assert "alias3    cat2         alias3        3" in strip_ansi(result.output)
        assert "alias2" not in strip_ansi(result.output)

    def test_unhide_commands(self, debug, mock_config):
        """Test unhiding commands."""
        # Given a populated database
        self._populate_database()

        # GIVEN a hidden command
        alias1 = Command.get(name="alias1")
        alias1.hidden = True
        alias1.save()

        # WHEN unhiding commands
        result = runner.invoke(app, ["--unhide", "1"])
        # debug("output", strip_ansi(result.output))

        # THEN the command is marked as unhidden
        assert result.exit_code == 0
        assert "Command alias1 unhidden" in strip_ansi(result.output)

        # WHEN listing commands
        result = runner.invoke(app, ["--list"])
        # debug("output", strip_ansi(result.output))

        # THEN the unhidden command is listed
        assert result.exit_code == 0
        assert "7 commands" in strip_ansi(result.output)
        assert "alias1" in strip_ansi(result.output)

    def test_recategorize(self, debug, mock_config):
        """Test recategorizing commands."""
        # Given a populated database
        self._populate_database()

        # WHEN recategorizing a command that doesn't exist
        result = runner.invoke(app, ["--categorize", "10000"])
        # debug("output", strip_ansi(result.output))

        # THEN the script should fail
        assert result.exit_code == 1

        # WHEN recategorizing a command
        result = runner.invoke(app, ["--categorize", "1"], input="2\ry\r")
        # debug("output", strip_ansi(result.output))

        # THEN the command is recategorized
        assert result.exit_code == 0
        assert "Command alias1 has been categorized to cat2" in strip_ansi(result.output)

        # WHEN viewing the command
        result = runner.invoke(app, ["alias1"])
        # debug("output", strip_ansi(result.output))

        # THEN the command is in the new category
        assert result.exit_code == 0
        assert "Categories:  cat2" in strip_ansi(result.output)

    def test_new_description(self, debug, mock_config):
        """Test recategorizing commands."""
        # Given a populated database
        self._populate_database()

        # WHEN editing a command that doesn't exist
        result = runner.invoke(app, ["--description", "10000"])
        # debug("output", strip_ansi(result.output))

        # THEN the script should fail
        assert result.exit_code == 1

        # WHEN editing the description of a command
        result = runner.invoke(app, ["--description", "1"], input="this is a new description\ry\r")
        # debug("output", strip_ansi(result.output))

        # THEN the command's description is updated
        assert result.exit_code == 0
        cmd = Command.get(1)
        assert cmd.description == "this is a new description"
