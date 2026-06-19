"""Tier selector: map a digit value to a glyph spec by regime.

  value < conventional_size              -> Conventional (a real character)
  conventional_size <= value < script_limit -> script GlyphOutline (engine.py)
  value >= script_limit                  -> data-matrix GlyphOutline

`all_procedural=True` forces even small values through the script engine (for a
fully self-contained novel alphabet). The cellular-automata regime (automata.py)
is available as an alternative generator but is not wired in by default yet.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from . import alphabet, engine, datamatrix
from .alphabet import CONVENTIONAL_SIZE
from .metrics import Metrics, DEFAULT
from .outline import GlyphOutline


@dataclass
class Conventional:
    """A digit that renders as a familiar character (regime 1)."""
    value: int
    char: str
    codepoint: int
    regime: str = "conventional"


GlyphSpec = Union[Conventional, GlyphOutline]


def glyph_for(value: int, *, metrics: Metrics = DEFAULT,
              conventional_size: int = CONVENTIONAL_SIZE,
              script_limit: int = 1_000_000,
              all_procedural: bool = False,
              namespace: int = 0) -> GlyphSpec:
    """Return the glyph spec for a single digit value."""
    if not all_procedural and value < conventional_size:
        c = alphabet.conventional_char(value)
        return Conventional(value=value, char=c, codepoint=ord(c))
    if script_limit is None or value < script_limit:
        return engine.glyph_outline(value, metrics, namespace=namespace)
    return datamatrix.datamatrix_outline(value, metrics)


def glyphs_for_number(value: int, base: int, **kw) -> List[GlyphSpec]:
    """Decompose `value` in `base` and return a glyph spec per digit (MSB first)."""
    return [glyph_for(d, **kw) for d in alphabet.to_digits(value, base)]
