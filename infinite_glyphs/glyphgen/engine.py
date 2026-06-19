"""Regime 2: the procedural calligraphic glyph engine.

Given an integer `value`, deterministically synthesize a script-like glyph from
a *vocabulary of stroke archetypes* (the way a real alphabet recombines a small
set of shapes): bowls, stems, arches, waves, diagonals, and ascender/descender
loops. Each archetype yields one or more pen centerlines; every centerline is
stroked with one broad-nib calligraphic pen (consistent angle per glyph) so the
result has thick/thin contrast and a hand-written feel.

Determinism: the same value always yields the same glyph (integer-seeded RNG, no
process-dependent str hashing). Distinctness: the archetype choice plus the rich
continuous parameter space keeps different values visually distinct.
"""
from __future__ import annotations

import math
import random
from typing import Callable, List, Tuple

from . import geometry as g
from .metrics import Metrics, DEFAULT
from .outline import GlyphOutline, Contour

# A "pen path" is a list of node points plus a width multiplier for that stroke.
PenPath = Tuple[List[Tuple[float, float]], float]


def _seed_for(value: int, namespace: int) -> int:
    """Stable integer seed (no str hashing -> reproducible across processes)."""
    return (value * 0x9E3779B1 + namespace * 0x85EBCA77 + 0xC2B2AE35) & 0x7FFFFFFFFFFF


def _nib_half_widths(centerline, base_pen, nib_angle, contrast):
    """Broad-nib width modulation: thin parallel to the nib, thick across it."""
    n = len(centerline)
    hws: List[float] = []
    for i in range(n):
        if i == 0:
            t = g.sub(centerline[1], centerline[0])
        elif i == n - 1:
            t = g.sub(centerline[-1], centerline[-2])
        else:
            t = g.sub(centerline[i + 1], centerline[i - 1])
        theta = math.atan2(t[1], t[0])
        w = base_pen * (contrast + (1.0 - contrast) * abs(math.sin(theta - nib_angle)))
        hws.append(w / 2.0)
    return hws


# ---------------------------------------------------------------------------
# Stroke archetypes -- each returns a list of PenPaths (node lists + width mult)
# ---------------------------------------------------------------------------

def _arch(rng, m) -> List[PenPath]:
    """n / m / h-like humps along the baseline."""
    L, R, lo, hi = m.writing_left, m.writing_right, m.baseline, m.x_height
    humps = rng.randint(1, 3)
    nodes = [(L - rng.uniform(0, 50), lo + rng.uniform(-20, 40))]
    span = (R - L) / humps
    for k in range(humps):
        x0 = L + k * span
        nodes.append((x0, lo + rng.uniform(0, 0.15) * (hi - lo)))
        nodes.append((x0 + span * rng.uniform(0.4, 0.6),
                      hi * rng.uniform(0.85, 1.05)))
    nodes.append((R, lo + rng.uniform(0, 0.18) * (hi - lo)))
    nodes.append((R + rng.uniform(0, 50), lo + rng.uniform(-20, 40)))
    return [(nodes, 1.0)]


def _bowl(rng, m) -> List[PenPath]:
    """o / c / e / a-like loop -- an ellipse, possibly left open (c/e)."""
    L, R, lo, hi = m.writing_left, m.writing_right, m.baseline, m.x_height
    cx = (L + R) / 2 + rng.uniform(-40, 40)
    cy = (lo + hi) / 2
    rx = (R - L) / 2 * rng.uniform(0.7, 0.95)
    ry = (hi - lo) / 2 * rng.uniform(0.92, 1.08)
    closed = rng.random() < 0.45
    start = rng.uniform(0.0, 0.4) * math.tau if not closed else 0.0
    gap = 0.0 if closed else rng.uniform(0.15, 0.5) * math.tau
    n = 14
    nodes = []
    sweep = math.tau - gap
    for k in range(n + 1):
        a = start + sweep * (k / n) + math.pi  # begin on the left (c-opening)
        nodes.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    paths: List[PenPath] = [(nodes, rng.uniform(0.9, 1.05))]
    # 'a'/'e' sometimes get a small tail or bar
    if rng.random() < 0.3:
        ty = cy + rng.uniform(-0.1, 0.1) * (hi - lo)
        paths.append(([(cx + rx * 0.2, ty), (R + rng.uniform(0, 40), lo + 30)],
                      rng.uniform(0.7, 0.9)))
    return paths


def _stem(rng, m) -> List[PenPath]:
    """l / t / i / f-like near-vertical stroke, optionally tall."""
    L, R, lo, hi = m.writing_left, m.writing_right, m.baseline, m.x_height
    x = (L + R) / 2 + rng.uniform(-90, 90)
    top = hi * rng.uniform(0.9, 1.0)
    if rng.random() < 0.5:
        top = m.ascender * rng.uniform(0.8, 1.0)  # tall (l/f/t)
    bow = rng.uniform(-60, 60)
    nodes = [(x - bow * 0.3, lo + rng.uniform(-10, 40)),
             (x, (lo + top) / 2),
             (x + bow, top)]
    if rng.random() < 0.4:  # a little foot/serif at the base
        nodes.insert(0, (x - rng.uniform(40, 90), lo + rng.uniform(0, 40)))
    paths: List[PenPath] = [(list(reversed(nodes)), rng.uniform(0.95, 1.1))]
    if rng.random() < 0.45:  # crossbar (t / f)
        cy = top * rng.uniform(0.6, 0.85)
        paths.append(([(x - rng.uniform(70, 130), cy + rng.uniform(-15, 15)),
                       (x + rng.uniform(70, 130), cy + rng.uniform(-15, 15))],
                      rng.uniform(0.6, 0.8)))
    return paths


def _wave(rng, m) -> List[PenPath]:
    """s / w / v-run-like undulation across the band."""
    L, R, lo, hi = m.writing_left, m.writing_right, m.baseline, m.x_height
    pts = rng.randint(4, 6)
    nodes = []
    for k in range(pts):
        frac = k / (pts - 1)
        x = L + frac * (R - L)
        y = lo + (hi - lo) * (0.5 + 0.55 * math.sin(frac * math.pi * rng.uniform(1.5, 3.0)
                                                     + rng.uniform(0, math.pi)))
        nodes.append((x, y))
    nodes.insert(0, (L - rng.uniform(0, 40), lo + rng.uniform(0, 60)))
    nodes.append((R + rng.uniform(0, 40), lo + rng.uniform(0, 60)))
    return [(nodes, rng.uniform(0.9, 1.05))]


def _diagonal(rng, m) -> List[PenPath]:
    """v / x / z / k-like crossing diagonals."""
    L, R, lo, hi = m.writing_left, m.writing_right, m.baseline, m.x_height
    paths: List[PenPath] = []
    n_strokes = rng.randint(1, 2)
    for _ in range(n_strokes):
        if rng.random() < 0.5:
            a = (L + rng.uniform(0, 60), hi * rng.uniform(0.85, 1.0))
            b = (R - rng.uniform(0, 60), lo + rng.uniform(0, 60))
        else:
            a = (L + rng.uniform(0, 60), lo + rng.uniform(0, 60))
            b = (R - rng.uniform(0, 60), hi * rng.uniform(0.85, 1.0))
        mid = ((a[0] + b[0]) / 2 + rng.uniform(-40, 40),
               (a[1] + b[1]) / 2 + rng.uniform(-40, 40))
        paths.append(([a, mid, b], rng.uniform(0.9, 1.05)))
    return paths


def _loop_desc(rng, m) -> List[PenPath]:
    """g / j / y / q / p-like body with a descender tail (sometimes looped)."""
    L, R, lo, hi = m.writing_left, m.writing_right, m.baseline, m.x_height
    base = _bowl(rng, m) if rng.random() < 0.6 else _arch(rng, m)
    dx = (L + R) / 2 + rng.uniform(-60, 120)
    tail = [(dx, hi * rng.uniform(0.3, 0.6)),
            (dx + rng.uniform(-30, 30), lo - 20),
            (dx + rng.uniform(-70, 30), m.descender * rng.uniform(0.7, 1.0)),
            (dx + rng.uniform(0, 90), m.descender * rng.uniform(0.3, 0.6))]
    base.append((tail, rng.uniform(0.75, 0.95)))
    return base


def _loop_asc(rng, m) -> List[PenPath]:
    """b / d / h / k / l-like body with an ascender loop."""
    L, R, lo, hi = m.writing_left, m.writing_right, m.baseline, m.x_height
    ax = (L + R) / 2 + rng.uniform(-90, 60)
    loop = [(ax, hi * rng.uniform(0.3, 0.5)),
            (ax - rng.uniform(20, 60), m.ascender * rng.uniform(0.7, 0.85)),
            (ax + rng.uniform(20, 70), m.ascender * rng.uniform(0.9, 1.0)),
            (ax + rng.uniform(50, 110), hi * rng.uniform(0.4, 0.7)),
            (ax + rng.uniform(0, 60), lo + rng.uniform(0, 60))]
    paths: List[PenPath] = [(loop, rng.uniform(0.9, 1.05))]
    if rng.random() < 0.6:
        paths += _bowl(rng, m)[:1]
    return paths


_ARCHETYPES: List[Callable] = [
    _arch, _bowl, _stem, _wave, _diagonal, _loop_desc, _loop_asc,
]


def glyph_outline(value: int, metrics: Metrics = DEFAULT, *,
                  namespace: int = 0) -> GlyphOutline:
    """Build a deterministic calligraphic glyph outline for `value`."""
    rng = random.Random(_seed_for(value, namespace))
    m = metrics

    # one nib per glyph -> coherent calligraphic identity.
    # `contrast` is the thin/thick ratio floor: keep it high enough that thin
    # strokes stay legible in a real font rasterizer (low values vanish at text
    # size and read as wispy hairlines).
    nib_angle = math.radians(rng.uniform(28, 52))
    base_pen = m.pen_width * rng.uniform(0.95, 1.25)
    contrast = rng.uniform(0.42, 0.60)

    # primary archetype, occasionally with a compatible decorative dot
    primary = rng.choice(_ARCHETYPES)
    pen_paths: List[PenPath] = primary(rng, m)

    if rng.random() < 0.22:  # i/j-style dot, kept sparing
        cx = (m.writing_left + m.writing_right) / 2 + rng.uniform(-120, 120)
        cy = m.x_height + rng.uniform(70, 150)
        # represent the dot as a tiny closed path handled below as a disc
        pen_paths.append(([("DOT", cx, cy, rng.uniform(34, 52))], 0.0))

    contours: List[Contour] = []
    for nodes, wmult in pen_paths:
        # special-cased dot marker
        if nodes and isinstance(nodes[0], tuple) and len(nodes[0]) == 4 and nodes[0][0] == "DOT":
            _, cx, cy, r = nodes[0]
            contours.append(g.disc((cx, cy), r))
            continue
        if len(nodes) < 2:
            continue
        centerline = g.catmull_rom(nodes, samples_per_seg=18)
        # guard against degenerate (near-zero-length) strokes -> avoids artifacts
        total = sum(g.length(g.sub(centerline[i + 1], centerline[i]))
                    for i in range(len(centerline) - 1))
        if total < m.pen_width * 0.6:
            continue
        hws = _nib_half_widths(centerline, base_pen * wmult, nib_angle, contrast)
        contours.append(g.stroke(centerline, hws, round_caps=True))

    if not contours:  # fallback so every value gets *some* mark
        centerline = g.catmull_rom(_arch(rng, m)[0][0], samples_per_seg=18)
        hws = _nib_half_widths(centerline, base_pen, nib_angle, contrast)
        contours.append(g.stroke(centerline, hws, round_caps=True))

    xs = [p[0] for c in contours for p in c]
    xmax = max(xs) if xs else m.writing_right
    advance = int(min(m.units_per_em, max(xmax + m.right_margin, m.writing_right + 20)))

    return GlyphOutline(value=value, contours=contours,
                        advance_width=advance, regime="script")
