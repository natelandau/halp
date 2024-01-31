[![PyPI version](https://badge.fury.io/py/halper.svg)](https://badge.fury.io/py/halper) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/halper) [![Python Code Checker](https://github.com/natelandau/halp/actions/workflows/automated-tests.yml/badge.svg)](https://github.com/natelandau/halp/actions/workflows/automated-tests.yml) [![codecov](https://codecov.io/gh/natelandau/halp/graph/badge.svg?token=GQ0UO3YCJO)](https://codecov.io/gh/natelandau/halp)

# Halp

Halp is a command line tool that reminds you how to use your custom shell commands. It finds aliases and functions from your dotfiles and indexes them so you can query them later. Simply type `halp <command>` to see what it does or `halp --list` to see all your custom commands.

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
halp <command>
```

See full output of a command

```bash
halp --full  <command>
```

List all your custom commands

```bash
halp --list
```

View all commands in a particular category

```bash
halp --category <category>
```

Index your dotfiles

```bash
halp --index
```

Hide commands that you don't want to see

```bash
halp --hide <command ID>,<command ID>,...
```

Customize the description of a command

```bash
halp --description <command ID>
```

Edit the configuration file

```bash
halp --edit-config
```

Search for commands who's code matches a regex pattern

```bash
halp --search-code <regex pattern>
```

See all options

```bash
halp --help
```

## Installation

Note: Halp requires Python 3.10 or higher.

[pipx](https://pipx.pypa.io/) is strongly recommended for installing Halp

```bash
pipx install halper
```

If pipx is not an option, you can install Halp in your Python user directory.

```bash
python -m pip install --user halper
```

## First run

Before you can use Halp, you must first

1. Create a configuration file by running `halp --edit-config``.
2. Index your commands. You can do this by running `halp --index``.

## Known issues

-   Does not associate comments with a command on the following line
-   If your function is written with parentheses instead of curly braces, it will not be parsed. ie `func command() (some code)`
-   Does not resolve if statements. ie `if [ -n "$BASH_VERSION" ]; then`. Consequently, if a command is wrapped in an if statement, it will still be indexed. Use `--hide` to hide unwanted commands.
-   Does not follow `source` or `.` directives within files
-   Tested on Bash and ZSH files only. Dotfiles for other shells may not work as expected.

## Configuration

On first run, a TOML configuration file will be created for you.

IMPORTANT: You must add at least one path to the `file_globs` list and then run `halp --index`. Otherwise, no commands will be indexed.

```toml
case_sensitive            = false           # Whether or not to match case sensitively with regexes
command_name_ignore_regex = ''              # Exclude commands who's names match this regex
comment_placement         = "BEST"          # Where you place comments to describe your code. One of "BEST", "ABOVE", "INLINE"
file_exclude_regex        = ''              # Exclude files who's paths match this regex
file_globs                = []              # Absolute path globs to files to parse for commands
uncategorized_name        = "uncategorized" # The name of the uncategorized category

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

# Contributing

## Setup: Once per project

1. Install Python 3.11 and [Poetry](https://python-poetry.org)
2. Clone this repository. `git clone https://some.url/to/the/package.git`
3. Install the Poetry environment with `poetry install`.
4. Activate your Poetry environment with `poetry shell`.
5. Install the pre-commit hooks with `pre-commit install --install-hooks`.

## Developing

-   This project follows the [Conventional Commits](https://www.conventionalcommits.org/) standard to automate [Semantic Versioning](https://semver.org/) and [Keep A Changelog](https://keepachangelog.com/) with [Commitizen](https://github.com/commitizen-tools/commitizen).
    -   When you're ready to commit changes run `cz c`
-   Run `poe` from within the development environment to print a list of [Poe the Poet](https://github.com/nat-n/poethepoet) tasks available to run on this project. Common commands:
    -   `poe lint` runs all linters
    -   `poe test` runs all tests with Pytest
-   Run `poetry add {package}` from within the development environment to install a run time dependency and add it to `pyproject.toml` and `poetry.lock`.
-   Run `poetry remove {package}` from within the development environment to uninstall a run time dependency and remove it from `pyproject.toml` and `poetry.lock`.
-   Run `poetry update` from within the development environment to upgrade all dependencies to the latest versions allowed by `pyproject.toml`.
