"""Font metrics for the glyph engine.

All glyph coordinates live in font units with the y-axis pointing UP
(standard font convention). One em = `units_per_em`. These metrics define
the writing zone the procedural engine draws into and the spacing a baked
font will use.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Metrics:
    units_per_em: int = 1000      # standard TrueType em size
    baseline: int = 0             # y of the baseline
    descender: int = -200         # lowest a descender (j, g tails) should reach
    x_height: int = 480           # top of the main writing band
    cap_height: int = 700         # top of tall letters
    ascender: int = 720           # highest an ascender flourish should reach
    left_margin: int = 110        # left side bearing
    right_margin: int = 110       # right side bearing
    pen_width: int = 64           # nominal calligraphic nib thickness (font units)

    @property
    def writing_left(self) -> int:
        return self.left_margin

    @property
    def writing_right(self) -> int:
        return self.units_per_em - self.right_margin

    @property
    def writing_width(self) -> int:
        return self.writing_right - self.writing_left


DEFAULT = Metrics()
