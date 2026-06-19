"""infinite-glyphs: a tiered glyph system for arbitrarily large numeral bases.

Three regimes, auto-selected by digit value (see provider.py):
  1. conventional - real characters (0-9 a-z A-Z) for small digit values
  2. script       - procedural calligraphic glyphs (engine.py)
  3. data-matrix  - dot-grid encodings that scale with bit-length (datamatrix.py)

All regimes emit the same `GlyphOutline` (vector contours in font units, y-up),
so SVG rendering, PNG rasterization, and TTF/OTF baking share one pipeline.
"""
from __future__ import annotations

from .outline import GlyphOutline
from .metrics import Metrics, DEFAULT

__all__ = ["GlyphOutline", "Metrics", "DEFAULT"]
