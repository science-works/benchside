"""Renderer protocol, the plain implementation, and the test recorder.

The contract: plain and rich renderers produce identical wording; they differ
only in ANSI and styling. Plain output is exact-string testable.
"""

from typing import IO, Protocol

from benchside.cli.ui._glyphs import default_glyphs


class Renderer(Protocol):
    def header(self, text: str) -> None: ...
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
