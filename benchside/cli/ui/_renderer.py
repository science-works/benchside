"""Renderer protocol, the plain implementation, and the test recorder.

The contract: plain and rich renderers produce identical wording; they differ
only in ANSI and styling. Plain output is exact-string testable.
"""

import textwrap
from typing import IO, Protocol

from benchside.cli.ui._glyphs import default_glyphs


class Renderer(Protocol):
    def header(self, text: str) -> None: ...
    def section(self, title: str, *, meta: str | None = None) -> None: ...
    def block(self, text: str, *, dim: bool = False) -> None: ...
    def info(self, text: str) -> None: ...
    def detail(self, text: str) -> None: ...
    def success(self, text: str) -> None: ...
    def warn(self, text: str) -> None: ...
    def error(self, headline: str, *, cause: str | None, hint: str | None) -> None: ...
    def table(self, columns: list[str], rows: list[list[str]]) -> None: ...


class PlainRenderer:
    """Sequential lines, no ANSI. Same wording as the rich renderer."""

    def __init__(self, file: IO[str]) -> None:
        self._file = file
        self._glyphs = default_glyphs()

    def _line(self, text: str) -> None:
        self._file.write(text + "\n")

    def header(self, text: str) -> None:
        self._line(f"── {text}")

    def section(self, title: str, *, meta: str | None = None) -> None:
        suffix = f"  {meta}" if meta else ""
        self._line("")
        self._line(f"{title.upper()}{suffix}")

    def block(self, text: str, *, dim: bool = False) -> None:
        lines = textwrap.wrap(text, width=76, break_long_words=False, break_on_hyphens=False) or [
            ""
        ]
        for line in lines:
            self._line(f"│ {line}")

    def info(self, text: str) -> None:
        self._line(text)

    def detail(self, text: str) -> None:
        self._line(f"  {text}")

    def success(self, text: str) -> None:
        self._line(f"{self._glyphs.check} {text}")

    def warn(self, text: str) -> None:
        self._line(f"{self._glyphs.warn} {text}")

    def error(self, headline: str, *, cause: str | None, hint: str | None) -> None:
        self._line(f"{self._glyphs.cross} {headline}")
        if cause:
            self._line(f"  {cause}")
        if hint:
            self._line(f"{self._glyphs.arrow} {hint}")

    def table(self, columns: list[str], rows: list[list[str]]) -> None:
        widths = [
            max(len(str(columns[i])), *(len(str(r[i])) for r in rows)) if rows else len(columns[i])
            for i in range(len(columns))
        ]
        self._line("  ".join(c.ljust(widths[i]) for i, c in enumerate(columns)).rstrip())
        for row in rows:
            self._line("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)).rstrip())


class RecordingRenderer:
    """Appends (event, payload) tuples; asserts sequence independent of format."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def header(self, text: str) -> None:
        self.events.append(("header", {"text": text}))

    def section(self, title: str, *, meta: str | None = None) -> None:
        self.events.append(("section", {"title": title, "meta": meta}))

    def block(self, text: str, *, dim: bool = False) -> None:
        self.events.append(("block", {"text": text, "dim": dim}))

    def info(self, text: str) -> None:
        self.events.append(("info", {"text": text}))

    def detail(self, text: str) -> None:
        self.events.append(("detail", {"text": text}))

    def success(self, text: str) -> None:
        self.events.append(("success", {"text": text}))

    def warn(self, text: str) -> None:
        self.events.append(("warn", {"text": text}))

    def error(self, headline: str, *, cause: str | None, hint: str | None) -> None:
        self.events.append(("error", {"headline": headline, "cause": cause, "hint": hint}))

    def table(self, columns: list[str], rows: list[list[str]]) -> None:
        self.events.append(("table", {"columns": columns, "rows": rows}))
