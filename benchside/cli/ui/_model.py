"""The UI facade. Renderer-agnostic; owns the TTY gate.

Chrome goes through this class to stderr. Data (JSON, markers, hook context
injection) never comes through here — it stays on stdout via bare print.
"""

import os
import sys
from typing import IO

from benchside.cli.ui._renderer import PlainRenderer, Renderer


def _should_use_rich(file: IO[str]) -> bool:
    try:
        is_tty = file.isatty()
    except (AttributeError, ValueError):
        is_tty = False
    return (
        is_tty
        and not os.environ.get("NO_COLOR")
        and not os.environ.get("CI")
        and os.environ.get("TERM") != "dumb"
    )


class UI:
    def __init__(self, *, renderer: Renderer) -> None:
        self._renderer = renderer

    @classmethod
    def create(cls, *, file: IO[str] | None = None, force_plain: bool | None = None) -> "UI":
        file = file if file is not None else sys.stderr
        use_rich = not force_plain if force_plain is not None else _should_use_rich(file)
        if use_rich:
            from benchside.cli.ui._rich import RichRenderer  # lazy: only path importing rich

            return cls(renderer=RichRenderer(file))
        return cls(renderer=PlainRenderer(file))

    def header(self, text: str) -> None:
        self._renderer.header(text)

    def info(self, text: str) -> None:
        self._renderer.info(text)

    def detail(self, text: str) -> None:
        self._renderer.detail(text)

    def success(self, text: str) -> None:
        self._renderer.success(text)

    def warn(self, text: str) -> None:
        self._renderer.warn(text)

    def error(self, headline: str, *, cause: str | None = None, hint: str | None = None) -> None:
        self._renderer.error(headline, cause=cause, hint=hint)

    def table(self, columns: list[str], rows: list[list[str]]) -> None:
        self._renderer.table(columns, rows)
