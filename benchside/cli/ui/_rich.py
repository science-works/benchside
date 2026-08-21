"""The rich renderer — the ONLY module in benchside allowed to import rich.

Same wording as PlainRenderer; adds color. No markup parsing (highlight off),
no live regions yet: every bench command is sub-second.
"""

from typing import IO

from rich.console import Console
from rich.table import Table
from rich.text import Text

from benchside.cli.ui._glyphs import default_glyphs


class RichRenderer:
    def __init__(self, file: IO[str]) -> None:
        self._console = Console(file=file, highlight=False, soft_wrap=True)
        self._glyphs = default_glyphs()

    def info(self, text: str) -> None:
        self._console.print(text)

    def detail(self, text: str) -> None:
        self._console.print(Text(f"  {text}", style="dim"))

    def success(self, text: str) -> None:
        self._console.print(Text(f"{self._glyphs.check} ", style="green") + Text(text))

    def warn(self, text: str) -> None:
        self._console.print(Text(f"{self._glyphs.warn} {text}", style="yellow"))

    def error(self, headline: str, *, cause: str | None, hint: str | None) -> None:
        self._console.print(
            Text(f"{self._glyphs.cross} ", style="red") + Text(headline, style="bold")
        )
        if cause:
            self._console.print(Text(f"  {cause}", style="dim"))
        if hint:
            self._console.print(Text(f"{self._glyphs.arrow} {hint}", style="cyan"))

    def table(self, columns: list[str], rows: list[list[str]]) -> None:
        table = Table(
            box=None, show_header=True, header_style="dim", pad_edge=False, padding=(0, 2, 0, 0)
        )
        for column in columns:
            table.add_column(column)
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        self._console.print(table)
