# type: ignore
"""Test the text parsers which use Parsy."""

from textwrap import dedent

import pytest

from halper.constants import CommandType
from halper.utils import settings
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
@pytest.mark.no_db
def test_parse_alias(comment_placement, input, return_value, mock_config) -> None:
    """Verify that alias parsing handles different comment placements correctly."""
    # Given: Configure comment placement setting
    settings.update(mock_config(comment_placement=comment_placement))

    # When: Parse the alias definition
    result = parse_alias.parse(input)

    # Then: Verify parsed output matches expected structure
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
@pytest.mark.no_db
def test_parse_export(comment_placement, input, return_value, mock_config) -> None:
    """Verify that export statements are parsed according to configured comment placement rules."""
    # Given: Configure how comments should be extracted from export statements
    settings.update(mock_config(comment_placement=comment_placement))

    # When: Parse an export statement with comments in various positions
    result = parse_export.parse(input)

    # Then: Ensure the parser extracts the correct name, value and description based on comment placement
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
@pytest.mark.no_db
def test_parse_function(comment_placement, input, return_value, mock_config) -> None:
    """Verify that function parsing extracts descriptions from comments based on configured placement."""
    # Given: Configure parser to use specific comment placement strategy
    settings.update(mock_config(comment_placement=comment_placement))

    # When: Parse a function definition with comments in various locations
    result = parse_function.parse(input)

    # Then: Verify parser extracts correct description based on comment placement
    assert result == return_value


@pytest.mark.no_db
def test_parse_comments_in_functions() -> None:
    """Verify that parse_file correctly extracts function descriptions from different comment styles and placements."""
    # Given: Shell functions with various comment styles and placements
    text = dedent("""
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

        """)

    # When: Parse the text containing multiple function definitions
    result = parse_file.many().parse(text)

    # Then: Verify each function is parsed with correct description based on comment style
    # Function with no comments should have no description
    assert result[0] == {
        "args": "",
        "code": 'echo "Hello World";',
        "command_type": CommandType.FUNCTION,
        "description": None,
        "name": "no_comment",
    }

    # Function with top comment should use it as description
    assert result[1] == {
        "name": "match_top_comment",
        "args": "",
        "code": '\n    # This is a top comment\n    echo "Hello World" # This is a comment\n    echo "something else"\n    # end function',
        "description": "This is a top comment",
        "command_type": CommandType.FUNCTION,
    }

    # Function with only inline/end comments should have no description
    assert result[2] == {
        "name": "no_matching_comments",
        "args": "",
        "code": '\n    echo "Hello World";\n    # Comment\n    echo "something else" # comment',
        "description": None,
        "command_type": CommandType.FUNCTION,
    }

    # Function with structured comment block should use DESC field as description
    assert result[3] == {
        "name": "structured_comment",
        "args": "",
        "code": '\n\n    # DESC:   This is a structured comment with a description\n    # ARGS:   None\n    # USAGE:  structured_comment [options]\n    echo "Hello World"; # comment\n    # comment\n    echo "something else"',
        "description": "This is a structured comment with a description",
        "command_type": CommandType.FUNCTION,
    }


@pytest.mark.no_db
def test_parse_file(mock_config) -> None:
    """Verify that parse_file correctly extracts and categorizes shell commands with their descriptions."""
    # Given: A shell script containing mixed command types and comment styles
    settings.update(mock_config(comment_placement="best"))

    # When: Parse the entire script content
    result = parse_file.many().parse(SAMPLE_FILE)

    # Then: Verify commands are correctly categorized by type
    aliases = [i for i in result if i["command_type"] == CommandType.ALIAS]
    exports = [i for i in result if i["command_type"] == CommandType.EXPORT]
    functions = [i for i in result if i["command_type"] == CommandType.FUNCTION]

    # Verify expected number of each command type was found
    assert len(aliases) == 3
    assert len(exports) == 3
    assert len(functions) == 3

    # Verify each command was parsed with correct metadata and description based on comment placement
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
