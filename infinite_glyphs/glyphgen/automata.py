"""Cellular-automata glyphs: a single scalable visual language.

An elementary (1D, 2-state, 3-neighbor) cellular automaton evolves an initial
row of bits into a 2D pattern. We seed the initial row with the value's binary
digits, so the grid width grows with bit-length (uniqueness for arbitrarily
large values -- the same information-theoretic scaling as the data-matrix
regime) and a fixed rule gives every glyph a coherent "physics". The CA amplifies
even a sparse seed into a rich pattern, so small values still look substantial.

Deterministic (value -> seed -> evolution) and distinct (different seeds evolve
differently). Output is vector squares, so it bakes into a font like any glyph.
"""
from __future__ import annotations

from typing import List

from .metrics import Metrics, DEFAULT
from .outline import GlyphOutline, Contour


def _square(x0: float, y0: float, x1: float, y1: float) -> Contour:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def evolve(value: int, width: int, height: int, rule: int,
           wrap: bool = False) -> List[List[int]]:
    """Run an elementary CA. Initial row = value's bits (LSB at left)."""
    row = [(value >> i) & 1 for i in range(width)]
    grid = [row[:]]
    for _ in range(height - 1):
        new = [0] * width
        for i in range(width):
            if wrap:
                l, r = row[(i - 1) % width], row[(i + 1) % width]
            else:
                l = row[i - 1] if i > 0 else 0
                r = row[i + 1] if i < width - 1 else 0
            idx = (l << 2) | (row[i] << 1) | r
            new[i] = (rule >> idx) & 1
        row = new
        grid.append(row[:])
    return grid


def ca_outline(value: int, metrics: Metrics = DEFAULT, *, rule: int = 30,
               min_width: int = 9, wrap: bool = False) -> GlyphOutline:
    """Render `value` as a cellular-automaton pattern of vector squares."""
    m = metrics
    width = max(min_width, value.bit_length() or 1)
    if width % 2 == 0:
        width += 1  # odd width keeps a single-seed pattern centered
    height = width
    grid = evolve(value, width, height, rule, wrap)

    region = min(m.writing_width, m.cap_height)
    x_left = (m.units_per_em - region) / 2
    y_bot = m.baseline + (m.cap_height - region) / 2
    top = y_bot + region
    step = region / width
    gap = step * 0.12

    contours: List[Contour] = []
    for r in range(height):
        for c in range(width):
            if not grid[r][c]:
                continue
            cx0 = x_left + c * step + gap / 2
            cx1 = x_left + (c + 1) * step - gap / 2
            cy1 = top - r * step - gap / 2          # row 0 at the top
            cy0 = top - (r + 1) * step + gap / 2
            contours.append(_square(cx0, cy0, cx1, cy1))

    return GlyphOutline(value=value, contours=contours,
                        advance_width=m.units_per_em, regime=f"ca{rule}")
