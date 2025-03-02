"""Test the parser module."""

import re

import pytest

from halper.constants import UNCATEGORIZED_NAME, CommandType
from halper.models import Category, File, Parser
from halper.utils import settings


def test_parser_instantiation(fixture_file) -> None:
    """Verify that Parser correctly initializes with a file path and creates a database record."""
    # Given: Create a test file
    test_file = fixture_file()

    # When: Instantiate a new Parser with the test file
    parser = Parser(test_file)

    # Then: Verify parser attributes are set correctly
    assert parser.path == test_file
    assert parser.path.exists()
    assert parser.regex_flags == re.IGNORECASE

    # And: Verify database record was created
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
    fixture_file,
    code_regex,
    comment_regex,
    command_name_regex,
    path_regex,
    cat_two_code_regex,
    found_categories,
) -> None:
    """Verify that commands are correctly categorized based on regex pattern matches."""
    # Given: Create two categories with different regex patterns
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

    # Given: Set up a command to test categorization
    command_to_parse = {"name": "ls", "code": "ls -l", "description": "comment text"}

    # Given: Initialize parser with test file
    test_file = fixture_file()
    p = Parser(test_file)

    # When: Categorize the command
    result = p._categorize_command(command_to_parse)

    # Then: Verify command is assigned to correct categories based on regex matches
    # Commands with no matches should be uncategorized
    if len(found_categories) == 0:
        assert result == [Category.get(name=UNCATEGORIZED_NAME)]
    # Commands matching one pattern should be in one category
    if len(found_categories) == 1:
        assert result == [Category.get(name=found_categories[0])]
    # Commands matching multiple patterns should be in multiple categories
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
def test_parser_parse(mock_config, fixture_file, file_content, expected):
    """Verify that Parser.parse() correctly extracts and categorizes commands from file content."""
    # Given: Set up test categories and file with command content
    # Create two categories - one that matches 'ls' commands and one empty category
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

    # Create test file with provided content and configure to ignore commands starting with '_'
    test_file = fixture_file(file_content)
    settings.update(mock_config(command_name_ignore_regex="_"))

    # When: Parse the file content
    p = Parser(test_file)
    result = p.parse()

    # Then: Verify parsed commands match expected output
    if not expected:
        # Files with no valid commands should return empty list
        assert result == expected
    else:
        # Valid commands should have correct metadata and be linked to file record
        assert result[0]["code"] == expected[0]["code"]
        assert result[0]["description"] == expected[0]["description"]
        assert result[0]["name"] == expected[0]["name"]
        assert result[0]["file"] == File.get(1)
        assert result[0]["command_type"] == expected[0]["command_type"]
