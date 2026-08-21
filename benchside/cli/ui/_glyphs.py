"""Glyph vocabulary. One place; two palettes."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GlyphSet:
    check: str
    cross: str
    warn: str
    arrow: str
    dot: str


UNICODE = GlyphSet(check="✓", cross="✗", warn="⚠", arrow="→", dot="•")
ASCII = GlyphSet(check="+", cross="x", warn="!", arrow="->", dot="*")


def default_glyphs() -> GlyphSet:
    return ASCII if os.name == "nt" else UNICODE
