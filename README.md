[![PyPI version](https://badge.fury.io/py/halper.svg)](https://badge.fury.io/py/halper) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/halper) [![Python Code Checker](https://github.com/natelandau/halp/actions/workflows/automated-tests.yml/badge.svg)](https://github.com/natelandau/halp/actions/workflows/automated-tests.yml) [![codecov](https://codecov.io/gh/natelandau/halp/graph/badge.svg?token=GQ0UO3YCJO)](https://codecov.io/gh/natelandau/halp)

# Halp

If you're anything like me, you have numerous shell aliases and functions in your dotfiles that you've written to make your life easier. You've also probably forgotten what half of them are called and how to use them. Halper aims to solve that problem by providing a single command that will print all your custom commands with a brief description of what they do.

Point Halp at the appropriate dotfiles and it will index all your custom commands and add them to categories you specify. Then you can query it to find your commands and their usage.

Key features:

-   Understands aliases, functions, and exported environment variables
-   Customizable categories
-   Customizable regexes for matching commands
-   Uses a SQLite database for fast querying

As an added bonus, it will also query [TLDR pages](https://tldr.sh/) for any commands that you don't have a custom command for. To enable this feature you must have a TLDR client installed and in your PATH. I recommend [TealDeer](https://github.com/dbrgn/tealdeer)

## Usage

Remind yourself what a command does

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

Hide a command that you don't want to see

```bash
halp --hide <command ID>
```

Edit the configuration file

```bash
halp --edit-config
```

See all options

```bash
halp --help
```

## Installation

Halp requires Python 3.10 or higher.

Install with Pip

```bash
pip install halper
```

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
case_sensitive            = false # Whether or not to match case sensitively with regexes
command_name_ignore_regex = ''    # Exclude commands who's names match this regex
file_exclude_regex        = ''    # Exclude files who's paths match this regex
file_globs                = []    # Globs to match files which will be indexed for commands

[categories] # Commands are matched against these categories
    [categories.example]
        category_name = "" # The name of the category
        code_regex    = '' # Regex to match within the code
        comment_regex = '' # Regex to match a comment on the same line as an alias/function definition or a comment on the first line of a function
        description   = "" # The description of this category
        name_regex    = '' # Regex to match the name of the command
        path_regex    = '' # Regex to match the path of the file
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
