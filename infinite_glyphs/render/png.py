"""PNG rasterization of glyph outlines via Pillow.

Uses an even-odd scanline fill (so loops/holes punch through correctly) with
supersampling for antialiasing. Independent of any system font, so what you see
is exactly the geometry the engine produced.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from infinite_glyphs.glyphgen.outline import GlyphOutline
from infinite_glyphs.glyphgen.metrics import Metrics, DEFAULT

Point = Tuple[float, float]


def _load_ttf(px: int):
    for name in ("arial.ttf", "Arial.ttf", "segoeui.ttf", "DejaVuSans.ttf",
                 r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(name, px)
        except Exception:
            continue
    return ImageFont.load_default()


def rasterize(contours: Sequence[Sequence[Point]],
              window: Tuple[float, float, float, float],
              out_w: int, out_h: int,
              supersample: int = 4,
              ink: int = 0, bg: int = 255) -> Image.Image:
    """Fill `contours` (font units, y-up) into an out_w x out_h grayscale image.

    `window` is (xmin, ymin, xmax, ymax) in font units mapped to the image with
    aspect preserved and centered. Even-odd rule across all contours together.
    """
    W, H = out_w * supersample, out_h * supersample
    img = Image.new("L", (W, H), bg)
    px = img.load()

    xmin, ymin, xmax, ymax = window
    span_x = max(xmax - xmin, 1e-6)
    span_y = max(ymax - ymin, 1e-6)
    scale = min(W / span_x, H / span_y)
    # center the content in the cell
    off_x = (W - span_x * scale) / 2
    off_y = (H - span_y * scale) / 2

    def tx(p: Point) -> Point:
        x = off_x + (p[0] - xmin) * scale
        y = H - (off_y + (p[1] - ymin) * scale)  # flip y (font up -> image down)
        return (x, y)

    edges: List[Tuple[Point, Point]] = []
    for c in contours:
        if len(c) < 2:
            continue
        tp = [tx(p) for p in c]
        for i in range(len(tp)):
            a = tp[i]
            b = tp[(i + 1) % len(tp)]
            if a[1] != b[1]:
                edges.append((a, b))

    if edges:
        # Nonzero winding rule: a stroked ribbon that self-intersects stays
        # solid (even-odd would punch spurious holes at sharp joints). Each
        # crossing carries a direction (+1 up, -1 down); fill where winding != 0.
        for y in range(H):
            yc = y + 0.5
            crossings: List[Tuple[float, int]] = []
            for a, b in edges:
                ay, by = a[1], b[1]
                if (ay <= yc < by) or (by <= yc < ay):
                    t = (yc - ay) / (by - ay)
                    x = a[0] + t * (b[0] - a[0])
                    crossings.append((x, 1 if by > ay else -1))
            if not crossings:
                continue
            crossings.sort()
            wind = 0
            for i in range(len(crossings) - 1):
                wind += crossings[i][1]
                if wind != 0:
                    xa = int(math.ceil(crossings[i][0] - 0.5))
                    xb = int(math.floor(crossings[i + 1][0] - 0.5))
                    for x in range(max(0, xa), min(W - 1, xb) + 1):
                        px[x, y] = ink

    if supersample > 1:
        img = img.resize((out_w, out_h), Image.LANCZOS)
    return img


def glyph_image(glyph: GlyphOutline, size: int = 160,
                metrics: Metrics = DEFAULT, supersample: int = 4) -> Image.Image:
    """Render one glyph on a shared baseline/scale window (descender..ascender)."""
    window = (0.0, float(metrics.descender),
              float(metrics.units_per_em), float(metrics.ascender))
    return rasterize(glyph.contours, window, size, size, supersample=supersample)


def contact_sheet(glyphs: Sequence[GlyphOutline], cols: int = 8,
                  cell: int = 150, pad: int = 6, label: bool = True,
                  metrics: Metrics = DEFAULT) -> Image.Image:
    """Grid of glyphs with value labels -- the visual QA tool."""
    n = len(glyphs)
    rows = (n + cols - 1) // cols
    label_h = 18 if label else 0
    cw, ch = cell + pad * 2, cell + pad * 2 + label_h
    sheet = Image.new("L", (cols * cw, rows * ch), 255)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    window = (0.0, float(metrics.descender),
              float(metrics.units_per_em), float(metrics.ascender))
    for idx, gly in enumerate(glyphs):
        r, c = divmod(idx, cols)
        gx, gy = c * cw + pad, r * ch + pad
        gimg = rasterize(gly.contours, window, cell, cell, supersample=4)
        sheet.paste(gimg, (gx, gy))
        # baseline guide
        bx0, bx1 = c * cw, c * cw + cw
        if label and font is not None:
            tag = f"{gly.value} [{gly.regime[:4]}]"
            draw.text((c * cw + 4, r * ch + cell + pad + 3), tag, fill=80, font=font)
    return sheet


def render_number(specs, metrics: Metrics = DEFAULT, glyph_px: int = 180,
                  gap_px: int = 14, pad: int = 24, supersample: int = 4):
    """Render a full number (list of GlyphSpec) as one horizontal PNG strip.

    Conventional digits draw as the real character (normal font); script and
    data-matrix digits rasterize from their outlines -- the mixed output a baked
    font would produce.
    """
    from infinite_glyphs.glyphgen.provider import Conventional

    m = metrics
    h_units = m.ascender - m.descender
    scale = glyph_px / h_units

    cells = []          # (kind, payload, cell_w_px)
    for spec in specs:
        if isinstance(spec, Conventional):
            adv = int(m.units_per_em * 0.6)
            cells.append(("char", spec.char, int(adv * scale)))
        else:
            cells.append(("glyph", spec, int(spec.advance_width * scale)))

    total_w = sum(w for _, _, w in cells) + gap_px * (len(cells) - 1) + pad * 2
    total_h = glyph_px + pad * 2
    img = Image.new("L", (max(total_w, 1), total_h), 255)

    char_font = _load_ttf(int(m.cap_height * scale))
    draw = ImageDraw.Draw(img)
    baseline_y = pad + int(m.ascender * scale)  # font baseline in image space

    x = pad
    window = (0.0, float(m.descender), float(m.units_per_em), float(m.ascender))
    for kind, payload, w in cells:
        if kind == "char":
            draw.text((x + w / 2, baseline_y), payload, fill=0,
                      font=char_font, anchor="ms")
        else:
            gimg = rasterize(payload.contours,
                             (0.0, float(m.descender), float(payload.advance_width),
                              float(m.ascender)),
                             w, glyph_px, supersample=supersample)
            img.paste(gimg, (x, pad))
        x += w + gap_px
    return img
