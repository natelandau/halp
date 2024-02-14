# type: ignore
"""Test the text parsers which use Parsy."""

import pytest

from halper.config import HalpConfig
from halper.constants import CommandType
from halper.utils.text_parsers import parse_alias, parse_export, parse_file, parse_function

SAMPLE_FILE = """

# This is a sample document containing
# 3 exports
# 3 functions
# 3 aliases

    # comment above
    EXPORT PATH=one

# comment above
alias one='one'

some other text

# comment above
one() {
    # comment inline
    builtin cd "$@" || return 1
    ll
}


export TEXT="two" # comment inline

    # comment above
    function two() {
        echo "Hello World";
    }

    alias ls='two' # comment inline [arg]

function three() {echo "Hello World"; }

alias ls='three'
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
            "alias ls='ls -l' # comment is [here]\n",
            {"name": "ls", "code": "ls -l", "description": "comment is [here]"},
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
def test_parse_alias(comment_placement, input, return_value, mock_specific_config) -> None:
    """Test the parse_alias function."""
    with HalpConfig.change_config_sources(
        mock_specific_config(comment_placement=comment_placement)
    ):
        result = parse_alias.parse(input)
        assert result == return_value


@pytest.mark.parametrize(
    ("comment_placement", "input", "return_value"),
    [
        # CommentPlacement.BEST
        (
            "best",
            "  export PATH=$PATH:/usr/local/bin\n",
            {"name": "PATH", "code": "$PATH:/usr/local/bin", "description": None},
        ),
        (
            "best",
            'export PATH="$PATH:/usr/local/bin"\n',
            {"name": "PATH", "code": "$PATH:/usr/local/bin", "description": None},
        ),
        (
            "best",
            "export PATH='$PATH:/usr/local/bin' # comment is here\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": "comment is here",
            },
        ),
        (
            "best",
            "# comment 1\nexport PATH='$PATH:/usr/local/bin'\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": "comment 1",
            },
        ),
        (
            "best",
            "# comment 1\nexport PATH='$PATH:/usr/local/bin' # comment 2\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": "comment 2",
            },
        ),
        # CommentPlacement.ABOVE
        (
            "above",
            "  export PATH=$PATH:/usr/local/bin\n",
            {"name": "PATH", "code": "$PATH:/usr/local/bin", "description": None},
        ),
        (
            "above",
            'export PATH="$PATH:/usr/local/bin"\n',
            {"name": "PATH", "code": "$PATH:/usr/local/bin", "description": None},
        ),
        (
            "above",
            "export PATH='$PATH:/usr/local/bin' # comment is here\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": None,
            },
        ),
        (
            "above",
            "# comment 1\nexport PATH='$PATH:/usr/local/bin'\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": "comment 1",
            },
        ),
        (
            "above",
            "# comment 1\nexport PATH='$PATH:/usr/local/bin' # comment 2\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": "comment 1",
            },
        ),
        # CommentPlacement.INLINE
        (
            "inline",
            "  export PATH=$PATH:/usr/local/bin\n",
            {"name": "PATH", "code": "$PATH:/usr/local/bin", "description": None},
        ),
        (
            "inline",
            'export PATH="$PATH:/usr/local/bin"\n',
            {"name": "PATH", "code": "$PATH:/usr/local/bin", "description": None},
        ),
        (
            "inline",
            "export PATH='$PATH:/usr/local/bin' # comment 1\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": "comment 1",
            },
        ),
        (
            "inline",
            "# comment 1\nexport PATH='$PATH:/usr/local/bin'\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": None,
            },
        ),
        (
            "inline",
            "# comment 1\nexport PATH='$PATH:/usr/local/bin' # comment 2\n",
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": "comment 2",
            },
        ),
    ],
)
def test_parse_export(comment_placement, input, return_value, mock_specific_config) -> None:
    """Test the parse_export function."""
    with HalpConfig.change_config_sources(
        mock_specific_config(comment_placement=comment_placement)
    ):
        result = parse_export.parse(input)
        assert result == return_value


@pytest.mark.parametrize(
    ("comment_placement", "input", "return_value"),
    [
        # CommentPlacement.BEST
        (
            "best",
            'func foo() {echo "foo ${bar:-default}" }',
            {"name": "foo", "args": "", "code": 'echo "foo ${bar:-default}"', "description": None},
        ),
        (
            "best",
            '   function foo()\n{echo "Hello World"; }',
            {"name": "foo", "args": "", "code": 'echo "Hello World";', "description": None},
        ),
        (
            "best",
            'foo(one, two) {echo "Hello World"\n}',
            {"name": "foo", "args": "one, two", "code": 'echo "Hello World"', "description": None},
        ),
        (
            "best",
            '# comment 1\n  foo() \n{\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\necho "Hello World"\n',
                "description": "comment 1",
            },
        ),
        (
            "best",
            'foo() {\n# comment 1\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\n# comment 1\necho "Hello World"\n',
                "description": "comment 1",
            },
        ),
        (
            "best",
            '# comment 1\n  foo() \n{\n# comment 2\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\n# comment 2\necho "Hello World"\n',
                "description": "comment 2",
            },
        ),
        # CommentPlacement.ABOVE
        (
            "above",
            '# comment 1\n  foo() \n{\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\necho "Hello World"\n',
                "description": "comment 1",
            },
        ),
        (
            "above",
            'foo() {\n# comment 1\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\n# comment 1\necho "Hello World"\n',
                "description": None,
            },
        ),
        (
            "above",
            '# comment 1\n  foo() \n{\n# comment 2\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\n# comment 2\necho "Hello World"\n',
                "description": "comment 1",
            },
        ),
        # CommentPlacement.INLINE
        (
            "inline",
            '# comment 1\n  foo() \n{\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\necho "Hello World"\n',
                "description": None,
            },
        ),
        (
            "inline",
            'foo() {\n# comment 1\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\n# comment 1\necho "Hello World"\n',
                "description": "comment 1",
            },
        ),
        (
            "inline",
            '# comment 1\n  foo() \n{\n# comment 2\necho "Hello World"\n\n}',
            {
                "name": "foo",
                "args": "",
                "code": '\n# comment 2\necho "Hello World"\n',
                "description": "comment 2",
            },
        ),
    ],
)
def test_parse_function(comment_placement, input, return_value, mock_specific_config) -> None:
    """Test the parse_function function."""
    with HalpConfig.change_config_sources(
        mock_specific_config(comment_placement=comment_placement)
    ):
        result = parse_function.parse(input)
        assert result == return_value


def test_parse_comments_in_functions(mock_config) -> None:
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


def test_parse_file(mock_specific_config) -> None:
    """Test the parse_file function."""
    with HalpConfig.change_config_sources(mock_specific_config(comment_placement="best")):
        result = parse_file.many().parse(SAMPLE_FILE)

        aliases = [i for i in result if i["command_type"] == CommandType.ALIAS]
        exports = [i for i in result if i["command_type"] == CommandType.EXPORT]
        functions = [i for i in result if i["command_type"] == CommandType.FUNCTION]

        assert len(aliases) == 3
        assert len(exports) == 3
        assert len(functions) == 3

        assert result == [
            {
                "name": "PATH",
                "code": "one",
                "description": "comment above",
                "command_type": CommandType.EXPORT,
            },
            {
                "name": "one",
                "code": "one",
                "description": "comment above",
                "command_type": CommandType.ALIAS,
            },
            {
                "name": "one",
                "args": "",
                "code": '\n    # comment inline\n    builtin cd "$@" || return 1\n    ll',
                "description": "comment inline",
                "command_type": CommandType.FUNCTION,
            },
            {
                "name": "TEXT",
                "code": "two",
                "description": "comment inline",
                "command_type": CommandType.EXPORT,
            },
            {
                "name": "two",
                "args": "",
                "code": '\n        echo "Hello World";\n   ',
                "description": "comment above",
                "command_type": CommandType.FUNCTION,
            },
            {
                "name": "ls",
                "code": "two",
                "description": "comment inline [arg]",
                "command_type": CommandType.ALIAS,
            },
            {
                "name": "three",
                "args": "",
                "code": 'echo "Hello World";',
                "description": None,
                "command_type": CommandType.FUNCTION,
            },
            {
                "name": "ls",
                "code": "three",
                "description": None,
                "command_type": CommandType.ALIAS,
            },
            {
                "name": "PATH",
                "code": "$PATH:/usr/local/bin",
                "description": None,
                "command_type": CommandType.EXPORT,
            },
        ]
