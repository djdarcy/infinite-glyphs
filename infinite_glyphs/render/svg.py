"""SVG rendering of glyph outlines and full numbers.

Outlines live in font units (y-up); SVG is y-down, so contours are wrapped in a
flip transform. Conventional digits render as <text> (the real character in a
normal font), script/data-matrix digits as filled <path>s -- the same mixed
output a baked font would produce.
"""
from __future__ import annotations

from typing import List, Sequence

from infinite_glyphs.glyphgen.metrics import Metrics, DEFAULT
from infinite_glyphs.glyphgen.outline import GlyphOutline
from infinite_glyphs.glyphgen.provider import Conventional, GlyphSpec


def path_d(contours) -> str:
    parts: List[str] = []
    for c in contours:
        if len(c) < 2:
            continue
        d = "M %.1f %.1f " % (c[0][0], c[0][1])
        d += " ".join("L %.1f %.1f" % (x, y) for x, y in c[1:])
        d += " Z"
        parts.append(d)
    return " ".join(parts)


def _flip(metrics: Metrics) -> str:
    # font y-up -> svg y-down: svg_y = ascender - y
    return f'translate(0,{metrics.ascender}) scale(1,-1)'


def glyph_svg(glyph: GlyphOutline, metrics: Metrics = DEFAULT,
              ink: str = "#111111") -> str:
    """Standalone SVG for one outline glyph."""
    m = metrics
    h = m.ascender - m.descender
    w = glyph.advance_width
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}">\n'
        f'  <g transform="{_flip(m)}" fill="{ink}">\n'
        f'    <path d="{path_d(glyph.contours)}"/>\n'
        f'  </g>\n</svg>\n'
    )


def number_svg(specs: Sequence[GlyphSpec], metrics: Metrics = DEFAULT,
               ink: str = "#111111", gap: int = 40,
               text_font: str = "monospace") -> str:
    """SVG for a full number: a horizontal run of mixed-regime digit glyphs."""
    m = metrics
    h = m.ascender - m.descender
    body: List[str] = []
    x = 0
    for spec in specs:
        if isinstance(spec, Conventional):
            adv = int(m.units_per_em * 0.6)
            # baseline is at svg-y = ascender; place text there
            body.append(
                f'  <text x="{x + adv/2:.0f}" y="{m.ascender}" '
                f'font-family="{text_font}" font-size="{int(m.cap_height)}" '
                f'text-anchor="middle" fill="{ink}">{spec.char}</text>'
            )
        else:
            adv = spec.advance_width
            body.append(
                f'  <g transform="translate({x},0) {_flip(m)}" fill="{ink}">'
                f'<path d="{path_d(spec.contours)}"/></g>'
            )
        x += adv + gap
    total_w = max(x - gap, 1)
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {h}" '
            f'width="{total_w}" height="{h}">\n')
    return head + "\n".join(body) + "\n</svg>\n"
