# type: ignore
"""Test the parser module."""

import pytest

from halper.config import HalpConfig
from halper.constants import CommandType
from halper.models import Category, Command, CommandCategory, File, Parser

# @pytest.fixture(autouse=True)
# def _bypass_functions(mocker):
#     """Bypass functionality which requires a production environment."""
#     mocker.patch("halper.cli.validate_config", return_value=None)


@pytest.mark.usefixtures("mock_db")
class TestParserClass:
    """Test the Parser Class."""

    def _clear_tests(self):
        """Clear the database ."""
        tables = [CommandCategory, Command, File, Category]
        for table in tables:
            for t in table.select():
                t.delete_instance(recursive=True, delete_nullable=True)

    def test_parser_instantiation(self, fixture_file, mock_specific_config) -> None:
        """Test the parser instantiation."""
        self._clear_tests()

        with HalpConfig.change_config_sources(mock_specific_config(case_sensitive=True)):
            # Create a test file
            test_file = fixture_file()

            # Instantiate the parser
            parser = Parser(test_file)
            assert parser.path == test_file
            assert parser.path.exists()
            assert parser.regex_flags == 0
            assert File.select().count() == 1
            assert parser.file == File.get()

    @pytest.mark.parametrize(
        (
            "code_regex",
            "comment_regex",
            "command_name_regex",
            "path_regex",
            "cat_two_code_regex",
            "found_categories",
        ),
        [
            ("", "", "", "", "", []),
            ("ls -l", "", "", "", "", ["cat_1"]),
            ("", "text", "", "", "", ["cat_1"]),
            ("", "", "^ls$", "", "", ["cat_1"]),
            ("", "", "", "test_file", "", ["cat_1"]),
            ("ls -l", "", "", "", "ls -l", ["cat_1", "cat_2"]),
        ],
    )
    def test__categorize_command(
        self,
        mock_config,
        fixture_file,
        code_regex,
        comment_regex,
        command_name_regex,
        path_regex,
        cat_two_code_regex,
        found_categories,
    ) -> None:
        self._clear_tests()
        # GIVEN categories in the database
        cat_1 = {
            "name": "cat_1",
            "code_regex": code_regex,
            "comment_regex": comment_regex,
            "command_name_regex": command_name_regex,
            "path_regex": path_regex,
            "description": "description text 1",
        }
        cat_2 = {
            "name": "cat_2",
            "code_regex": cat_two_code_regex,
            "comment_regex": "",
            "command_name_regex": "",
            "path_regex": "",
            "description": "description text 2",
        }
        Category.create(**cat_1)
        Category.create(**cat_2)

        # AND GIVEN a command to parse
        command_to_parse = {"name": "ls", "code": "ls -l", "description": "comment text"}

        # AND GIVEN an instantiated parser
        test_file = fixture_file()
        p = Parser(test_file)

        # WHEN the _categorize_command method is called
        result = p._categorize_command(command_to_parse)

        # THEN the correct categories should be returned
        if len(found_categories) == 0:
            assert result == [Category.get(name=HalpConfig().uncategorized_name)]
        if len(found_categories) == 1:
            assert result == [Category.get(name=found_categories[0])]
        if len(found_categories) == 2:
            assert result == [
                Category.get(name=found_categories[0]),
                Category.get(name=found_categories[1]),
            ]

    @pytest.mark.parametrize(
        ("file_content", "expected"),
        [
            ("xxxxx", []),
            (
                "alias ls='ls -l'\n",
                [
                    {
                        "code": "ls -l",
                        "command_type": CommandType.ALIAS,
                        "description": None,
                        "name": "ls",
                    },
                ],
            ),
            ("alias _ls='ls -l'\n", []),
            (
                "alias existing='existing' # comment\n",
                [
                    {
                        "code": "existing",
                        "command_type": CommandType.ALIAS,
                        "description": "comment",
                        "name": "existing",
                    },
                ],
            ),
        ],
    )
    def test_parser_parse(self, mock_specific_config, fixture_file, file_content, expected):
        """Test the parser parse() method."""
        self._clear_tests()
        # GIVEN categories in the database, a file, and a configuration file
        cat_1 = {
            "name": "cat_1",
            "code_regex": "ls",
            "comment_regex": "",
            "command_name_regex": "",
            "path_regex": "",
            "description": "description text 1",
        }
        cat_2 = {
            "name": "cat_2",
            "code_regex": "",
            "comment_regex": "",
            "command_name_regex": "",
            "path_regex": "",
            "description": "description text 2",
        }
        Category.create(**cat_1)
        Category.create(**cat_2)

        test_file = fixture_file(file_content)

        with HalpConfig.change_config_sources(mock_specific_config(command_name_ignore_regex="_")):
            # WHEN the parse method is called
            p = Parser(test_file)
            result = p.parse()

            # THEN the command should be categorized and added to the database
            if not expected:
                assert result == expected
            else:
                assert result[0]["code"] == expected[0]["code"]
                assert result[0]["description"] == expected[0]["description"]
                assert result[0]["name"] == expected[0]["name"]
                assert result[0]["file"] == File.get(1)
                assert result[0]["command_type"] == expected[0]["command_type"]
