# type: ignore
"""Test creating an index of commands."""

from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from halper.cli import app
from halper.config import HalpConfig
from halper.models import Category, Command, CommandCategory, Database, File
from tests.helpers import strip_ansi

runner = CliRunner()


@pytest.fixture(autouse=True)
def _bypass_functions(mocker):
    """Bypass functionality which requires a production environment."""
    mocker.patch.object(Database, "instantiate", MagicMock())
    mocker.patch("halper.cli.validate_config", return_value=None)


@pytest.mark.usefixtures("mock_db")
class TestIndexing:
    """Test indexing commands."""

    @staticmethod
    def _clear_test_data():
        """Clear test data from the database."""
        Category.delete().execute()
        File.delete().execute()
        Command.delete().execute()
        CommandCategory.delete().execute()

    @pytest.mark.parametrize(
        (
            "globs",  # Relative to tmp_path/fixtures/
            "exclude_regex",
            "case_sensitive",
            "categories",
            "num_files",
            "num_cats",
            "num_commands",
            "uncategorized_commands",
            "return_strings",
            "exit_code",
        ),
        [
            pytest.param(
                ["dotfiles/*.bash"],
                ".*exclude.*",
                False,
                {},
                4,
                0,
                19,
                19,
                ["🤷    No commands found in", "No categories from config"],
                0,
                id="Find all files/commands in fixtures",
            ),
            pytest.param(
                ["dotfiles/*.bash", "failed_path/**/*.bash"],
                ".*exclude.*",
                False,
                {},
                4,
                0,
                19,
                19,
                [
                    "🤷    No commands found in",
                    "No categories from config",
                    "🤷    Glob found no files:",
                ],
                0,
                id="Find all files/commands in fixtures, one glob fails",
            ),
            pytest.param(  # exclude ignore.bash and categorize from in code
                ["**/*.bash"],
                r".*ignore\.bash",
                False,
                {
                    "hello": {
                        "name": "hello world",
                        "code_regex": r"hello.*world",
                        "comment_regex": r"",
                        "description": "category",
                        "command_name_regex": "",
                        "path_regex": "",
                    }
                },
                3,
                1,
                13,
                9,
                ["🤷    No commands found in", "✅ 1  Categories from config"],
                0,
                id="exclude ignore.bash and categorize from in code",
            ),
            pytest.param(  # specific file glob, categorize from comments
                ["dotfiles/dotfiles_1.bash"],
                "",
                False,
                {
                    "always_print": {
                        "name": "hello world",
                        "code_regex": r"",
                        "comment_regex": r"Always.*contents",
                        "description": "category",
                        "command_name_regex": "",
                        "path_regex": "",
                    }
                },
                1,
                1,
                9,
                8,
                ["✅ 1 Categories from config"],
                0,
                id="specific file glob, categorize from comments",
            ),
            pytest.param(  # Find no files
                ["dotfiles/nonexistant.txt"],
                "",
                False,
                {
                    "always_print": {
                        "name": "hello world",
                        "code_regex": r"",
                        "comment_regex": r"Always.*contents",
                        "description": "category",
                        "command_name_regex": "",
                        "path_regex": "",
                    }
                },
                0,
                0,
                0,
                0,
                ["ERROR    | No files found matching the globs in your configuration."],
                1,
                id="Find no files",
            ),
            pytest.param(  # Find no commands
                ["dotfiles/no_commands.bash"],
                "",
                False,
                {},
                1,
                -1,  # -1 because Uncategorized is always created
                0,
                0,
                [
                    "❌   No commands indexed",
                    "✅ 1 Files parsed",
                    "❓   No categories from config",
                    "🤷   No commands found in",
                ],
                0,
                id="Find files but no commands",
            ),
            pytest.param(  # case sensitive
                ["dotfiles/dotfiles_1.bash"],
                ".*DOTFILES.*",
                True,
                {
                    "cat": {
                        "name": "cat",
                        "code_regex": "",
                        "comment_regex": "",
                        "description": "category",
                        "command_name_regex": ".*ALIAS.*",
                        "path_regex": "",
                    }
                },
                1,
                1,
                9,
                9,
                ["✅ 1 Categories from config"],
                0,
                id="case sensitive regex",
            ),
            pytest.param(  # Match name regex
                ["dotfiles/dotfiles_1.bash"],
                "",
                False,
                {
                    "cat": {
                        "name": "cat",
                        "code_regex": "",
                        "comment_regex": "",
                        "description": "category",
                        "command_name_regex": "ALIAS1",
                        "path_regex": "",
                    }
                },
                1,
                1,
                9,
                8,
                ["✅ 1 Categories from config"],
                0,
                id="Match name regex",
            ),
            pytest.param(  # Match path regex
                ["dotfiles/*.bash"],
                "",
                False,
                {
                    "cat": {
                        "name": "cat",
                        "code_regex": "",
                        "comment_regex": "",
                        "description": "category",
                        "command_name_regex": "",
                        "path_regex": "dotfiles_1",
                    }
                },
                4,
                1,
                19,
                10,
                ["✅ 1  Categories from config", "✅ 19 Commands indexed"],
                0,
                id="Match path regex",
            ),
        ],
    )
    def test_indexing(
        self,
        fixtures,
        mock_specific_config,
        globs,
        exclude_regex,
        case_sensitive,
        categories,
        num_files,
        num_cats,
        num_commands,
        uncategorized_commands,
        return_strings,
        exit_code,
        debug,
    ):
        """Test indexing commands."""
        self._clear_test_data()

        with HalpConfig.change_config_sources(
            mock_specific_config(
                file_globs=[f"{fixtures}/{glob}" for glob in globs],
                file_exclude_regex=exclude_regex,
                case_sensitive=case_sensitive,
                categories=categories,
            )
        ):
            # WHEN the index command is run
            result = runner.invoke(app, ["--index"])

            # THEN the output should be as expected
            assert result.exit_code == exit_code

            assert File.select().count() == num_files
            assert len(Category.select()) == num_cats + 1  # 'Uncategorized' always created
            assert Command.select().count() == num_commands

            if exit_code == 0 and num_commands > 0:
                assert (
                    CommandCategory.select()
                    .where(CommandCategory.category == Category.get(name="uncategorized"))
                    .count()
                    == uncategorized_commands
                )

            for string in return_strings:
                assert string in strip_ansi(result.output)

    def test_reindexing_hidden(self, fixture_file, mock_specific_config):
        """Test indexing commands maintaining hidden status."""
        self._clear_test_data()

        # GIVEN a dotfile
        test_file = fixture_file("alias one='echo one'\nalias two='echo two'\n")

        with HalpConfig.change_config_sources(mock_specific_config(file_globs=[f"{test_file}"])):
            # WHEN the index command is run
            result = runner.invoke(app, ["--index"])

            # THEN the command should run a first time
            assert result.exit_code == 0
            assert File.select().count() == 1
            assert Command.select().count() == 2

            # WHEN a command is set to "hidden" and halp --index is run again
            Command.update(hidden=True).where(Command.name == "two").execute()
            result = runner.invoke(app, ["--index"])

            # THEN the command should still be hidden
            assert result.exit_code == 0
            assert Command.select().where(Command.name == "two").get().hidden is True

            # WHEN a command is set to "hidden" and halp --index-full is run
            result = runner.invoke(app, ["--index-full"])

            # THEN the command should not be hidden
            assert result.exit_code == 0
            assert Command.select().where(Command.name == "two").get().hidden is False

    def test_reindexing_description(self, fixture_file, mock_specific_config):
        """Test indexing commands maintaining custom descriptions."""
        self._clear_test_data()

        # GIVEN a dotfile
        test_file = fixture_file(
            "alias one='echo one' # description\nalias two='echo two' # description\n"
        )

        with HalpConfig.change_config_sources(mock_specific_config(file_globs=[f"{test_file}"])):
            # WHEN the index command is run the first time
            result = runner.invoke(app, ["--index"])

            # THEN the description should be set
            assert result.exit_code == 0
            cmd = Command.get(name="one")
            assert cmd.description == "description"
            assert not cmd.has_custom_description

            # WHEN the description is updated and index is run again
            cmd.description = "new description"
            cmd.has_custom_description = True
            cmd.save()
            result = runner.invoke(app, ["--index"])

            # THEN the description should not be updated
            assert result.exit_code == 0
            cmd = Command.get(name="one")
            assert cmd.description == "new description"
            assert cmd.has_custom_description

    def test_reindexing_recategorization(self, fixture_file, mock_specific_config, debug):
        """Test indexing commands maintaining custom categories."""
        self._clear_test_data()

        # GIVEN a dotfile
        test_file = fixture_file(
            "alias one='echo one' # description\nalias two='echo two' # description\n"
        )

        with HalpConfig.change_config_sources(
            mock_specific_config(
                file_globs=[f"{test_file}"],
                categories={
                    "cat1": {
                        "name": "cat1",
                        "code_regex": "two",
                        "comment_regex": "",
                        "description": "category",
                        "command_name_regex": "",
                        "path_regex": "",
                    },
                    "cat2": {
                        "name": "cat2",
                        "code_regex": "two",
                        "comment_regex": "",
                        "description": "category",
                        "command_name_regex": "",
                        "path_regex": "",
                    },
                    "cat3": {
                        "name": "cat3",
                        "code_regex": "",
                        "comment_regex": "",
                        "description": "category",
                        "command_name_regex": "",
                        "path_regex": "",
                    },
                },
            )
        ):
            # WHEN the index command is run the first time
            result = runner.invoke(app, ["--index"])

            # THEN the command should be categorized
            assert result.exit_code == 0
            cc1 = CommandCategory.get(1)
            cc2 = CommandCategory.get(2)
            cc3 = CommandCategory.get(3)

            assert cc1.command.name == "one"
            assert cc1.category.name == HalpConfig().uncategorized_name
            assert cc2.command.name == "two"
            assert cc2.category.name == "cat1"
            assert cc3.command.name == "two"
            assert cc3.category.name == "cat2"
            assert CommandCategory.select().count() == 3

            # WHEN a command is recategorized and halp --index is run again
            CommandCategory.create(
                command=Command.get(Command.name == "two"),
                category=Category.get(Category.name == "cat3"),
                is_custom=True,
            )
            cc2.delete_instance()
            cc3.delete_instance()
            result = runner.invoke(app, ["--index"])

            # Then the command should still be categorized to the custom category
            assert result.exit_code == 0

            cc1 = CommandCategory.get(1)
            cc2 = CommandCategory.get(2)
            assert cc1.command.name == "one"
            assert cc1.category.name == HalpConfig().uncategorized_name
            assert cc2.command.name == "two"
            assert cc2.category.name == "cat3"
            assert CommandCategory.select().count() == 2
