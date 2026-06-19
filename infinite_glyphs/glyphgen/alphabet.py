"""Regime 1 (conventional characters) and base/digit decomposition.

For small digit values there is no reason to invent a glyph -- the familiar
characters are clearer than anything we could generate. The default conventional
set is base-62: 0-9, then a-z, then A-Z. Hex is simply its first 16 entries.
Digit values at or beyond the conventional size fall through to the procedural
regimes (script, then data-matrix).
"""
from __future__ import annotations

from typing import List

CONVENTIONAL = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
CONVENTIONAL_SIZE = len(CONVENTIONAL)  # 62


def to_digits(value: int, base: int) -> List[int]:
    """Decompose a non-negative integer into base-`base` digits, most-significant
    first. Each returned digit is an int in [0, base)."""
    if base < 2:
        raise ValueError("base must be >= 2")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return [0]
    out: List[int] = []
    while value:
        value, r = divmod(value, base)
        out.append(r)
    out.reverse()
    return out


def conventional_char(digit: int) -> str:
    """The familiar character for a digit value, or '' if beyond the set."""
    if 0 <= digit < CONVENTIONAL_SIZE:
        return CONVENTIONAL[digit]
    return ""


def is_conventional(digit: int, conventional_size: int = CONVENTIONAL_SIZE) -> bool:
    return 0 <= digit < conventional_size
