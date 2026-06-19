"""Regime 3: data-matrix glyphs for astronomically large digit values.

When a digit value exceeds what a procedural script could keep perceptibly
distinct, fall back to a dot grid that encodes the value's bits directly. The
grid side grows with bit-length (side = ceil(sqrt(bits))), so uniqueness holds
for arbitrarily large values -- the information-theoretic floor: N distinct
glyphs require >= log2(N) cells. A framing border gives it a contained "glyph"
look and fixes orientation; the result is still vector contours (one square per
set bit) so it bakes into a font like any other glyph.
"""
from __future__ import annotations

import math
from typing import List

from .metrics import Metrics, DEFAULT
from .outline import GlyphOutline, Contour


def grid_side_for(value: int, min_side: int = 3) -> int:
    """Square grid side needed to uniquely encode `value` (>=1 bit)."""
    bits = max(1, value.bit_length())
    return max(min_side, math.ceil(math.sqrt(bits)))


def _square(x0: float, y0: float, x1: float, y1: float) -> Contour:
    # counter-clockwise so all data cells share winding (nonzero fill = solid)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def datamatrix_outline(value: int, metrics: Metrics = DEFAULT, *,
                       min_side: int = 3, border: bool = True) -> GlyphOutline:
    """Encode `value` as a bordered dot grid of vector squares."""
    m = metrics
    side = grid_side_for(value, min_side)
    cells = side * side

    # bits of value, LSB-first, padded to the grid capacity
    bits = [(value >> i) & 1 for i in range(cells)]

    # square drawing region centered in the em (use the cap band for height)
    region = min(m.writing_width, m.cap_height)
    x_left = (m.units_per_em - region) / 2
    y_bot = (m.cap_height - region) / 2 + m.baseline
    step = region / side
    gap = step * 0.16  # spacing between cells

    contours: List[Contour] = []

    if border:
        # thin frame drawn as four bars (keeps a clean contained look)
        bw = max(step * 0.18, m.units_per_em * 0.012)
        x0, y0, x1, y1 = x_left, y_bot, x_left + region, y_bot + region
        contours.append(_square(x0, y0, x1, y0 + bw))           # bottom
        contours.append(_square(x0, y1 - bw, x1, y1))           # top
        contours.append(_square(x0, y0, x0 + bw, y1))           # left
        contours.append(_square(x1 - bw, y0, x1, y1))           # right
        # inset the data grid inside the frame
        inset = bw + step * 0.12
        x_left += inset
        y_bot += inset
        region -= 2 * inset
        step = region / side
        gap = step * 0.16

    for idx in range(cells):
        if not bits[idx]:
            continue
        r, c = divmod(idx, side)
        cx0 = x_left + c * step + gap / 2
        cy0 = y_bot + r * step + gap / 2
        cx1 = x_left + (c + 1) * step - gap / 2
        cy1 = y_bot + (r + 1) * step - gap / 2
        contours.append(_square(cx0, cy0, cx1, cy1))

    advance = m.units_per_em
    return GlyphOutline(value=value, contours=contours,
                        advance_width=advance, regime="datamatrix")
