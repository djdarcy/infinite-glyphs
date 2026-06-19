"""The shared glyph representation produced by every regime.

A GlyphOutline is a list of closed contours in font units with the y-axis
pointing UP (font convention). A contour is a list of (x, y) points; segments
between consecutive points are straight lines and the contour is implicitly
closed (last point connects back to first). Curves are flattened to fine line
segments upstream, which keeps the SVG / PNG / TTF backends uniform and simple.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

Point = Tuple[float, float]
Contour = List[Point]


@dataclass
class GlyphOutline:
    value: int
    contours: List[Contour]
    advance_width: int
    regime: str = "script"

    def bbox(self) -> Tuple[float, float, float, float]:
        """Return (xmin, ymin, xmax, ymax); (0,0,0,0) if empty."""
        pts = [p for c in self.contours for p in c]
        if not pts:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def point_count(self) -> int:
        return sum(len(c) for c in self.contours)
