"""Bake glyph outlines into an installable TrueType font.

A baked font is self-contained: every digit value in the chosen range gets a
generated glyph mapped to a code point (Private Use Area by default), so a number
encoded as that code-point string renders in any app once the font is installed.

The generator is pluggable (`outline_fn`): cursive today, cellular-automata or
any other regime later. One TTF holds up to 65,535 glyphs; for larger bases bake
a font set (multiple files) -- see plan in README.
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Optional

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from infinite_glyphs.glyphgen.engine import glyph_outline
from infinite_glyphs.glyphgen.metrics import Metrics, DEFAULT
from infinite_glyphs.glyphgen.outline import GlyphOutline

PUA_BMP_BASE = 0xE000          # 6,400 slots (U+E000..U+F8FF)
PUA_PLANE15_BASE = 0xF0000     # ~65,534 slots, for larger sets

MAX_GLYPHS_PER_FONT = 65535


def _draw(pen, contours) -> None:
    for c in contours:
        if len(c) < 2:
            continue
        pen.moveTo((round(c[0][0]), round(c[0][1])))
        for x, y in c[1:]:
            pen.lineTo((round(x), round(y)))
        pen.closePath()


def _notdef(m: Metrics):
    pen = TTGlyphPen(None)
    # a hollow box (outer CCW, inner CW hole)
    o = [(80, 0), (m.units_per_em - 80, 0),
         (m.units_per_em - 80, m.cap_height), (80, m.cap_height)]
    inset = 60
    i = [(80 + inset, inset), (80 + inset, m.cap_height - inset),
         (m.units_per_em - 80 - inset, m.cap_height - inset),
         (m.units_per_em - 80 - inset, inset)]
    _draw(pen, [o, i])
    return pen.glyph()


def encode_number(digits: Iterable[int], unicode_base: int = PUA_BMP_BASE) -> str:
    """Map digit values to the font's code-point string."""
    return "".join(chr(unicode_base + d) for d in digits)


def bake_font(values: Iterable[int], *,
              outline_fn: Callable[..., GlyphOutline] = glyph_outline,
              metrics: Metrics = DEFAULT,
              unicode_base: int = PUA_BMP_BASE,
              family: str = "Infinite Glyphs",
              style: str = "Regular",
              remove_overlaps: bool = True,
              filepath: Optional[str] = None):
    """Build a TTF containing a glyph for each value. Returns the FontBuilder.

    Codepoint for value v = unicode_base + v. Raises if the range overflows the
    chosen PUA block or exceeds one font's glyph limit. `remove_overlaps` boolean-
    unions each glyph's stroked ribbons into clean, consistently-wound contours
    (so they fill solid in real font rasterizers, not just our PNG backend).
    """
    values = list(values)
    if len(values) + 1 > MAX_GLYPHS_PER_FONT:
        raise ValueError(f"{len(values)} glyphs exceeds one-font limit "
                         f"({MAX_GLYPHS_PER_FONT}); bake a font set instead")

    m = metrics
    glyph_order = [".notdef"]
    glyfs = {".notdef": _notdef(m)}
    hmetrics = {".notdef": (m.units_per_em, 0)}
    cmap = {}

    for v in values:
        name = f"g{v}"
        glyph_order.append(name)
        gly = outline_fn(v, m)
        pen = TTGlyphPen(None)
        _draw(pen, gly.contours)
        glyfs[name] = pen.glyph()
        xmin = min((p[0] for c in gly.contours for p in c), default=0)
        hmetrics[name] = (gly.advance_width, int(round(xmin)))
        cp = unicode_base + v
        if cp > 0x10FFFF:
            raise ValueError(f"codepoint {cp:#x} for value {v} exceeds Unicode max")
        cmap[cp] = name

    fb = FontBuilder(m.units_per_em, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyfs)
    fb.setupHorizontalMetrics(hmetrics)
    fb.setupHorizontalHeader(ascent=m.ascender, descent=m.descender)
    fb.setupNameTable({
        "familyName": family,
        "styleName": style,
        "fullName": f"{family} {style}",
        "psName": f"{family.replace(' ', '')}-{style}",
        "version": "0.1",
    })
    fb.setupOS2(sTypoAscender=m.ascender, sTypoDescender=m.descender,
                usWinAscent=m.ascender, usWinDescent=-m.descender)
    fb.setupPost()

    if remove_overlaps:
        try:
            from fontTools.ttLib.removeOverlaps import removeOverlaps
            removeOverlaps(fb.font)
        except ImportError:
            pass  # skia-pathops not installed; ship with raw (may render thin)

    if filepath:
        fb.font.save(filepath)
    return fb
