"""Views for the indexer."""

from pathlib import Path

import inflect
from rich.markdown import Markdown
from rich.table import Table

from halper.models import IndexResult
from halper.utils import console

p = inflect.engine()


def index_command_view(result: IndexResult, *, show_all_files: bool = False) -> None:
    """Output the index command results."""
    console.rule("Indexing results")
    grid = Table.grid(expand=False, padding=(0, 1))
    grid.add_column()
    grid.add_column()
    grid.add_column()

    if len(result.categories) == 0:
        grid.add_row("❓", "", "No categories found")
    else:
        grid.add_row("✅", f"{len(result.categories)}", "Categories indexed")

    for glob_path, count in result.glob_paths.items():
        grid.add_row("📁", f"{count}", Markdown(f"Files found in `{glob_path}`"))

    for file_path, count in result.files.items():
        file_path_display = (
            f"~/{file_path.expanduser().resolve().relative_to(Path.home())}"
            if str(Path.home()) in str(file_path.expanduser().resolve())
            else file_path
        )

        if count == 0:
            grid.add_row(
                "🤷",
                "[dim]0[/dim]",
                Markdown(
                    f"Commands indexed in `{file_path_display}`",
                    style="dim",
                ),
            )
        elif show_all_files:
            grid.add_row(
                "🔍",
                f"[dim]{count}[/dim]",
                Markdown(
                    f"{p.plural('Command', count)} indexed in `{file_path_display}`",
                    style="dim",
                ),
            )

    grid.add_row("✅", f"[bold]{result.total_commands}[/bold]", "[bold]Commands indexed[/bold]")

    console.print(grid)
