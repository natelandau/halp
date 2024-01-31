"""Text parsers utilizing Parsy used to identify commands in text files."""

import re
from collections.abc import Generator

from parsy import generate, regex, string

from halper.config import HalpConfig
from halper.constants import CommandType, CommentPlacement

# Define shared grammar elements for parsing.
WS = regex(r"[ \t]+").desc("whitespace")
NEWLINE = regex(r"[\n\r]+").desc("newline")
EOL = WS.optional() >> NEWLINE
QUOTE = regex(r"['\"]")  # Match either a single or double quote
COMMENT_ON_LINE = WS.optional() >> string("#") >> WS.optional() >> regex(r"[^\n\r]*")
STANDALONE_COMMENT = (
    NEWLINE.many() >> WS.optional() >> string("#") >> WS.optional() >> regex(r"[^\n\r]*")
)


@generate
def parse_alias() -> Generator[None, None, dict[str, str | None]]:
    """Parse a string to extract an alias definition.

    The function looks for a line starting with 'alias', followed by the alias name, an equal sign,
    and the alias value. It supports optional single or double quotes around the alias value and
    optionally parses a comment at the end of the line. The function returns a dictionary with the
    alias name, value, and comment (if any).

    When CommentPlacement.BEST, we will favor inline comments over above comments.

    Returns:
        dict[str, str]: A dictionary containing 'name', 'code', and 'description' keys with corresponding
                        values extracted from the alias definition.
    """
    # Grammar
    alias_identifier = WS.optional() >> regex(r"alias", flags=re.IGNORECASE) << WS
    alias_name = regex(r"[^=\s\\\$`]+") << string("=")

    # Parse
    above_comment = None
    if HalpConfig().comment_placement in {CommentPlacement.BEST, CommentPlacement.ABOVE}:
        above_comment = yield STANDALONE_COMMENT.optional()
    else:
        yield STANDALONE_COMMENT.optional()

    yield NEWLINE.optional()

    yield alias_identifier
    name = yield alias_name

    quotation = None
    quotation = yield QUOTE.optional()

    if quotation == "'":
        value = yield regex(r"[^']+") << string("'")
    elif quotation == '"':
        value = yield regex(r'[^"]+') << string('"')
    elif quotation is None:
        value = yield regex(r"[^\s\n]+")

    inline_comment = None
    if HalpConfig().comment_placement in {CommentPlacement.INLINE, CommentPlacement.BEST}:
        inline_comment = yield COMMENT_ON_LINE.optional()
    else:
        yield COMMENT_ON_LINE.optional()

    yield NEWLINE.optional()

    return {"name": name, "code": value, "description": inline_comment or above_comment}


@generate
def parse_export() -> Generator[None, None, dict[str, str | None]]:
    """Parse a string to extract an export definition.

    Identifies an export statement, which starts with 'export', followed by a variable name, an equal
    sign, and the variable value. Handles optional single or double quotes around the variable value
    and an optional comment. Returns a dictionary with the export name, value, and comment.

    When CommentPlacement.BEST, we will favor inline comments over above comments.

    Returns:
        dict[str, str]: A dictionary containing 'name', 'code', and 'description' keys with values
                        extracted from the export definition.
    """
    # Grammar
    export_identifier = WS.optional() >> regex(r"export", flags=re.IGNORECASE) << WS
    export_name = regex(r"[^=\s\"'\$\\`]+") << string("=")

    # Parse
    yield NEWLINE.optional()

    above_comment = None
    if HalpConfig().comment_placement in {CommentPlacement.BEST, CommentPlacement.ABOVE}:
        above_comment = yield STANDALONE_COMMENT.optional()
    else:
        yield STANDALONE_COMMENT.optional()

    yield NEWLINE.optional()

    yield export_identifier
    name = yield export_name

    quotation = None
    quotation = yield QUOTE.optional()
    if quotation == "'":
        value = yield regex(r"[^']+") << string("'")
    elif quotation == '"':
        value = yield regex(r'[^"]+') << string('"')
    else:
        value = yield regex(r"[^\s\n]+")

    inline_comment = None
    if HalpConfig().comment_placement in {CommentPlacement.INLINE, CommentPlacement.BEST}:
        inline_comment = yield COMMENT_ON_LINE.optional()
    else:
        yield COMMENT_ON_LINE.optional()

    yield NEWLINE.optional()

    return {"name": name, "code": value, "description": inline_comment or above_comment}


@generate
def parse_function() -> Generator[None, None, dict[str, str | None]]:
    """Parse a string to extract a function definition.

    Looks for a function definition starting with an optional 'function' keyword, followed by the
    function name, arguments, and the function body enclosed in braces. Returns a dictionary
    containing the function's name, arguments, and body.

    Returns:
        dict[str, str]: A dictionary with 'name', 'args', 'code', and 'description' keys, representing the function's name, arguments, body, and comment respectively.
    """
    # Grammar
    func_identifier = WS.optional() >> regex(r"func(tion)?", flags=re.IGNORECASE).optional() << WS
    func_name = WS.optional() >> regex(r"[\w-]+") << string("(")
    func_args = regex(r"[^)]*") << string(")")
    func_start = string("{")
    func_body = regex(r".*?(?=[\s\n]\})", flags=re.DOTALL)
    func_end = regex(r"[\s]\}")

    # Parse
    above_comment = None
    if HalpConfig().comment_placement in {CommentPlacement.BEST, CommentPlacement.ABOVE}:
        above_comment = yield STANDALONE_COMMENT.optional()
    else:
        yield STANDALONE_COMMENT.optional()

    yield NEWLINE.optional()

    yield func_identifier.optional()
    name = yield func_name
    args = yield func_args
    yield regex(r"[\s]+").optional()
    yield func_start
    body = yield func_body

    inline_comment = None
    if HalpConfig().comment_placement in {CommentPlacement.INLINE, CommentPlacement.BEST}:
        inline_comment = parse_function_body_comment.parse(body)

    yield func_end

    return {
        "name": name,
        "args": args,
        "code": body,
        "description": inline_comment or above_comment,
    }


@generate
def parse_function_body_comment() -> Generator[None, None, str]:
    """Parse a string to extract a comment from a function body.

    Looks for a comment within a function body and returns it.

    Returns:
        str: The comment found in the function body.
    """
    # Grammar
    structured_start = (
        regex(r"desc(ription)?", flags=re.IGNORECASE)
        << WS.optional()
        << regex(r"[-:=]")
        << WS.optional()
    )
    comment = (
        NEWLINE.many()
        >> WS.optional()
        >> string("#")
        >> WS.optional()
        >> structured_start.optional()
        >> regex(r"[^\n\r]*")
    )

    any_further_text = regex(r".*", flags=re.DOTALL)

    comment = yield comment.optional()
    yield any_further_text

    return comment


@generate
def parse_file() -> Generator[None, None, dict[str, str | CommandType]]:
    """Parse a string to extract aliases, exports, and functions.

    Analyzes a given string to identify and extract shell script components, including aliases,
    exports, and functions.

    Returns:
        dict[str, str | CommandType]: A dictionary containing the parsed command details.
    """
    # Grammar

    # Match any line that does not start with 'alias', 'export', or 'function' and does not contain a function definition
    not_alias = regex(r"(?!([ \t]*#.*?[\n\r])?[ \t]*alias)", flags=re.IGNORECASE).desc("not_alias")
    not_export = regex(r"(?!([ \t]*#.*?[\n\r])?[ \t]*export [\w-]+=)", flags=re.IGNORECASE).desc(
        "not_export"
    )
    not_function = regex(
        r"(?!([ \t]*#.*?[\n\r])?[ \t]*(func(tion)? )?[\w-]+\(\))", flags=re.IGNORECASE
    ).desc("not_function")
    non_matching_line = (
        WS.optional() >> (not_alias + not_export + not_function) << regex(r".*") << NEWLINE
    ).desc("non_matching_line")

    # Parse
    yield non_matching_line.many().optional()
    yield NEWLINE.optional()

    # Find matching commands
    parser_results: tuple[CommandType, dict[str, str | CommandType]] | None = (
        yield parse_alias.tag(CommandType.ALIAS)
        | parse_export.tag(CommandType.EXPORT)
        | parse_function.tag(CommandType.FUNCTION)
    )

    # Add the tag to the result dictionary
    if parser_results is None:
        msg = "Parser results should not be None"
        raise ValueError(msg)

    result: dict[str, str | CommandType] = parser_results[1]
    result["command_type"] = parser_results[0]

    yield non_matching_line.many().optional()
    yield NEWLINE.optional()

    return result
