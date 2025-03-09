# Halp

[![Changelog](https://img.shields.io/github/v/release/natelandau/halp?include_prereleases&label=changelog)](https://github.com/natelandau/halp/releases) [![PyPI version](https://badge.fury.io/py/halper.svg)](https://badge.fury.io/py/halper) [![Tests](https://github.com/natelandau/halp/actions/workflows/test.yml/badge.svg)](https://github.com/natelandau/halp/actions/workflows/test.yml) [![codecov](https://codecov.io/gh/natelandau/halp/graph/badge.svg?token=NHBKL0B6CL)](https://codecov.io/gh/natelandau/halp)

Halp is a command line tool that reminds you how to use your custom shell commands. It finds aliases and functions from your dotfiles and indexes them so you can query them later. Simply type `halp search <command>` to see what the command does or `halp list` to see all your custom commands.

Point Halp at the appropriate dotfiles and it will index all your custom commands and add them to categories you specify. Then you can query it to find your commands and their usage.

Key features:

-   Understands your aliases, functions, and exported environment variables
-   Customizable categories
-   Uses your inline comments to describe your commands
-   Customizable regexes for matching commands
-   SQLite database used for fast querying
-   Explains builtin commands with [TLDR pages](https://tldr.sh/)
-   Explains builtin commands with options from [mankier.com](https://www.mankier.com/)

Note: To enable TLDR integration, you must have a TLDR client installed and in your PATH. I recommend [TealDeer](https://github.com/dbrgn/tealdeer)

## Usage

Remind yourself what a command does (Your own aliases and functions or TLDR pages)

```bash
halp search <command>
```

See full output of a command

```bash
halp search --full <command>
```

Search for commands who's code matches a regex pattern

```bash
halp --search-code <regex pattern>
```

List all your custom commands

```bash
halp list
```

View all commands in a particular category

```bash
halp list <category>
```

Index your dotfiles

```bash
halp index
```

Hide commands that you don't want to see

```bash
halp hide <command ID>,<command ID>,...
```

Unhide commands that you don't want to see

```bash
halp unhide <command ID>,<command ID>,...
```

Create a new configuration file

```bash
halp config
```

See all options

```bash
halp --help
```

## Installation

Note: Halp requires Python 3.10 or higher.

Install with [pipx](https://pipx.pypa.io/)

```bash
pipx install halper
```

Install with [uv](https://docs.astral.sh/uv/)

```bash
uv tool install halper
```

If pipx or uv is not an option, you can install Halp in your Python user directory.

```bash
python -m pip install --user halper
```

## First run

Before you can use Halp, you must first

1. Create a configuration file by running `halp config`.
2. Index your dotfiles by running `halp index`.

## File locations

Halp uses the [XDG specification](https://specifications.freedesktop.org/basedir-spec/latest/) for determining the locations of configuration files, logs, and caches.

-   Configuration file: `~/.config/halp/config.toml`
-   Database: `~/.local/share/halp/halp.sqlite`

## Known issues

-   Does not associate comments with a command on the following line
-   If your function is written with parentheses instead of curly braces, it will not be parsed. Use `func command() { some code }` instead of `func command() (some code)`
-   Does not resolve if statements. ie `if [ -n "$BASH_VERSION" ]; then`. Consequently, if a command is wrapped in an if statement, it will still be indexed. Use `halp hide` to hide unwanted commands.
-   Does not follow `source` or `.` directives within files
-   Tested on Bash and ZSH files only. Dotfiles for other shells may not work as expected.

## Configuration

On first run, a TOML configuration file will be created for you.

IMPORTANT: You must add at least one path to the `file_globs` list and then run `halp index`. Otherwise, no commands will be indexed.

```toml
command_name_ignore_regex = ''              # Exclude commands who's names match this regex
comment_placement         = "BEST"          # Where you place comments to describe your code. One of "BEST", "ABOVE", "INLINE"
file_exclude_regex        = ''              # Exclude files who's paths match this regex
file_globs                = []              # Absolute path globs to files to parse for commands

[categories] # Commands are matched against these categories
    [categories.example]
        name = "" # The name of the category
        code_regex    = '' # Regex to match within the code
        comment_regex = '' # Regex to match a comment on the same line as an alias/function definition or a comment on the first line of a function
        description   = "" # The description of this category
        command_name_regex    = '' # Regex to match the name of the command
        path_regex    = '' # Regex to match the path of the file
```

### How halp finds descriptions for commands

The `comment_placement` setting determines where Halp looks for comments to describe your commands. It can be one of the following: `BEST` (default), `ABOVE`, `INLINE`. When `BEST` is used, Halp will look for comments in both places and use the inline comment when both are found.

Here's how Halp looks for comments in each case:

```bash

# Description                            <------ Above
alias command='some code' # Description  <------ Inline

# Description                            <------ Above
func command() {
    # Description                        <------ Inline
    some code
}
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for more information.
