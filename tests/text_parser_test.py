# type: ignore
"""Test the text parsers which use Parsy."""

import pytest

from halper.config import HalpConfig
from halper.constants import CommandType, CommentPlacement
from halper.utils.text_parsers import parse_alias, parse_export, parse_file, parse_function

SAMPLE_FILE = """

# This is a sample document containing
# 3 exports
# 3 functions
# 3 aliases

EXPORT PATH=$PATH:/usr/local/bin

# comment 1
alias ls='ls -l'

# test a function
cd() {
    # Always print contents of directory when entering
    builtin cd "$@" || return 1
    ll
}
export TEXT="Hello World"

    function foo() {
        echo "Hello World";
    }

    alias ls='ls -l' # comment 2

function foo() {echo "Hello World"; }

alias ls='ls -l'
test

    export PATH=$PATH:/usr/local/bin

Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

"""


@pytest.mark.parametrize(
    ("comment_placement", "input", "return_value"),
    [
        # CommentPlacement.BEST
        (
            "best",
            "     ALIAS ls='ls -l'\n",
            {"name": "ls", "code": "ls -l", "description": None},
        ),
        (
            "best",
            'alias ls="ls -l"\n',
            {"name": "ls", "code": "ls -l", "description": None},
        ),
        (
            "best",
            "alias ls='ls -l' # comment is here\n",
            {"name": "ls", "code": "ls -l", "description": "comment is here"},
        ),
        (
            "best",
            "# comment 1\n    alias ls='ls -l' # comment 2\n",
            {"name": "ls", "code": "ls -l", "description": "comment 2"},
        ),
        (
            "best",
            " # comment is here\nalias ls='ls -l'\n",
            {"name": "ls", "code": "ls -l", "description": "comment is here"},
        ),
        # CommentPlacement.ABOVE
        (
            "above",
            "     ALIAS ls='ls -l'\n",
            {"name": "ls", "code": "ls -l", "description": None},
        ),
        (
            "above",
            'alias ls="ls -l"\n',
            {"name": "ls", "code": "ls -l", "description": None},
        ),
        (
            "above",
            "alias ls='ls -l' # comment is here\n",
            {"name": "ls", "code": "ls -l", "description": None},
        ),
        (
            "above",
            "# comment 1\n    alias ls='ls -l' # comment 2\n",
            {"name": "ls", "code": "ls -l", "description": "comment 1"},
        ),
        (
            "above",
            " # comment is here\nalias ls='ls -l'\n",
            {"name": "ls", "code": "ls -l", "description": "comment is here"},
        ),
        # CommentPlacement.INLINE
        (
            "inline",
            "     ALIAS ls='ls -l'\n",
            {"name": "ls", "code": "ls -l", "description": None},
        ),
        (
            "inline",
            'alias ls="ls -l"\n',
            {"name": "ls", "code": "ls -l", "description": None},
        ),
        (
            "inline",
            "alias ls='ls -l' # comment is here\n",
            {"name": "ls", "code": "ls -l", "description": "comment is here"},
        ),
        (
            "inline",
            "# comment 1\n    alias ls='ls -l' # comment 2\n",
            {"name": "ls", "code": "ls -l", "description": "comment 2"},
        ),
        (
            "inline",
            " # comment is here\nalias ls='ls -l'\n",
            {"name": "ls", "code": "ls -l", "description": None},
        ),
    ],
)
def test_parse_alias(comment_placement, input, return_value, config_data) -> None:
    """Test the parse_alias function."""
    with HalpConfig.change_config_sources(config_data(comment_placement=comment_placement)):
        result = parse_alias.parse(input)
        assert result == return_value


@pytest.mark.parametrize(
    ("input", "return_value"),
    [
        (
            "  export PATH=$PATH:/usr/local/bin\n",
            {"name": "PATH", "code": "$PATH:/usr/local/bin", "description": None},
        ),
        (
            'export PATH="$PATH:/usr/local/bin"\n',
            {"name": "PATH", "code": "$PATH:/usr/local/bin", "description": None},
        ),
        (
            "export PATH='$PATH:/usr/local/bin' # comment is here\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": "comment is here",
            },
        ),
    ],
)
def test_parse_export(input, return_value) -> None:
    """Test the parse_export function."""
    result = parse_export.parse(input)
    assert result == return_value


@pytest.mark.parametrize(
    ("input", "return_value"),
    [
        (
            'func foo() {echo "foo ${bar:-default}" }',
            {"name": "foo", "args": "", "code": 'echo "foo ${bar:-default}"', "description": None},
        ),
        (
            '   function foo() {echo "Hello World"; }',
            {"name": "foo", "args": "", "code": 'echo "Hello World";', "description": None},
        ),
        (
            'foo(one, two) {echo "Hello World"\n}',
            {"name": "foo", "args": "one, two", "code": 'echo "Hello World"', "description": None},
        ),
        (
            '  foo() \n{\necho "Hello World"\n\n}',
            {"name": "foo", "args": "", "code": '\necho "Hello World"\n', "description": None},
        ),
    ],
)
def test_parse_function(input, return_value) -> None:
    """Test the parse_function function."""
    result = parse_function.parse(input)
    assert result == return_value


def test_parse_comments_in_functions() -> None:
    """Test the parse_file function."""
    text = """
no_comment() {echo "Hello World"; }

match_top_comment() {
    # This is a top comment
    echo "Hello World" # This is a comment
    echo "something else"
    # end function
}

no_matching_comments() {
    echo "Hello World";
    # Comment
    echo "something else" # comment
}

structured_comment() {

    # DESC:   This is a structured comment with a description
    # ARGS:   None
    # USAGE:  structured_comment [options]
    echo "Hello World"; # comment
    # comment
    echo "something else"
}

"""
    result = parse_file.many().parse(text)

    assert result[0] == {
        "args": "",
        "code": 'echo "Hello World";',
        "command_type": CommandType.FUNCTION,
        "description": None,
        "name": "no_comment",
    }
    assert result[1] == {
        "name": "match_top_comment",
        "args": "",
        "code": '\n    # This is a top comment\n    echo "Hello World" # This is a comment\n    echo "something else"\n    # end function',
        "description": "This is a top comment",
        "command_type": CommandType.FUNCTION,
    }

    assert result[2] == {
        "name": "no_matching_comments",
        "args": "",
        "code": '\n    echo "Hello World";\n    # Comment\n    echo "something else" # comment',
        "description": None,
        "command_type": CommandType.FUNCTION,
    }

    assert result[3] == {
        "name": "structured_comment",
        "args": "",
        "code": '\n\n    # DESC:   This is a structured comment with a description\n    # ARGS:   None\n    # USAGE:  structured_comment [options]\n    echo "Hello World"; # comment\n    # comment\n    echo "something else"',
        "description": "This is a structured comment with a description",
        "command_type": CommandType.FUNCTION,
    }


# def test_parse_file() -> None:
#     """Test the parse_file function."""
#     result = parse_file.many().parse(SAMPLE_FILE)

#     aliases = [i for i in result if i["command_type"] == CommandType.ALIAS]
#     exports = [i for i in result if i["command_type"] == CommandType.EXPORT]
#     functions = [i for i in result if i["command_type"] == CommandType.FUNCTION]

#     assert len(aliases) == 3
#     assert len(exports) == 3
#     assert len(functions) == 3

#     assert result == [
#         {
#             "name": "PATH",
#             "code": "$PATH:/usr/local/bin",
#             "description": None,
#             "command_type": CommandType.EXPORT,
#         },
#         {
#             "name": "ls",
#             "code": "ls -l",
#             "description": "comment 1",
#             "command_type": CommandType.ALIAS,
#         },
#         {
#             "name": "cd",
#             "args": "",
#             "code": '\n    # Always print contents of directory when entering\n    builtin cd "$@" || return 1\n    ll',
#             "description": "Always print contents of directory when entering",
#             "command_type": CommandType.FUNCTION,
#         },
#         {
#             "name": "TEXT",
#             "code": "Hello World",
#             "description": None,
#             "command_type": CommandType.EXPORT,
#         },
#         {
#             "name": "foo",
#             "args": "",
#             "code": '\n        echo "Hello World";\n   ',
#             "description": None,
#             "command_type": CommandType.FUNCTION,
#         },
#         {
#             "name": "ls",
#             "code": "ls -l",
#             "description": "comment 2",
#             "command_type": CommandType.ALIAS,
#         },
#         {
#             "name": "foo",
#             "args": "",
#             "code": 'echo "Hello World";',
#             "description": None,
#             "command_type": CommandType.FUNCTION,
#         },
#         {
#             "name": "ls",
#             "code": "ls -l",
#             "description": None,
#             "command_type": CommandType.ALIAS,
#         },
#         {
#             "name": "PATH",
#             "code": "$PATH:/usr/local/bin",
#             "description": None,
#             "command_type": CommandType.EXPORT,
#         },
#     ]
