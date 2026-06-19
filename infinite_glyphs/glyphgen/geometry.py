"""Geometry primitives for the procedural script engine.

Pure-Python (no numpy) 2D helpers: vector ops, a centripetal Catmull-Rom
spline flattener (smooth curves through points), a variable-width stroker
(turns a pen centerline into a fillable closed contour, giving calligraphic
thick/thin contrast), and a disc generator for dots and bowls.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

Point = Tuple[float, float]


def sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def mul(a: Point, s: float) -> Point:
    return (a[0] * s, a[1] * s)


def length(a: Point) -> float:
    return math.hypot(a[0], a[1])


def normalize(a: Point) -> Point:
    l = length(a)
    return (a[0] / l, a[1] / l) if l > 1e-9 else (0.0, 0.0)


def catmull_rom(points: Sequence[Point], samples_per_seg: int = 18,
                alpha: float = 0.5) -> List[Point]:
    """Centripetal Catmull-Rom spline through `points` (open curve).

    Returns a flattened polyline passing through every input point. alpha=0.5
    is the centripetal parameterization, which avoids the cusps/self-intersection
    that the uniform version (alpha=0) produces on sharp turns.
    """
    pts = [(float(x), float(y)) for (x, y) in points]
    n = len(pts)
    if n <= 2:
        return pts[:]

    # Pad with reflected-ish endpoints so the curve reaches the first/last point.
    P = [pts[0]] + pts + [pts[-1]]
    out: List[Point] = []

    def next_t(t: float, pi: Point, pj: Point) -> float:
        d = length(sub(pj, pi))
        return t + max(d, 1e-6) ** alpha

    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0
        t1 = next_t(t0, p0, p1)
        t2 = next_t(t1, p1, p2)
        t3 = next_t(t2, p2, p3)
        if abs(t2 - t1) < 1e-9:
            continue
        for s in range(samples_per_seg):
            t = t1 + (t2 - t1) * (s / samples_per_seg)
            # Barry-Goldman pyramidal evaluation.
            A1 = add(mul(p0, (t1 - t) / (t1 - t0)), mul(p1, (t - t0) / (t1 - t0)))
            A2 = add(mul(p1, (t2 - t) / (t2 - t1)), mul(p2, (t - t1) / (t2 - t1)))
            A3 = add(mul(p2, (t3 - t) / (t3 - t2)), mul(p3, (t - t2) / (t3 - t2)))
            B1 = add(mul(A1, (t2 - t) / (t2 - t0)), mul(A2, (t - t0) / (t2 - t0)))
            B2 = add(mul(A2, (t3 - t) / (t3 - t1)), mul(A3, (t - t1) / (t3 - t1)))
            C = add(mul(B1, (t2 - t) / (t2 - t1)), mul(B2, (t - t1) / (t2 - t1)))
            out.append(C)
    out.append(pts[-1])
    return out


def _tangents(poly: Sequence[Point]) -> List[Point]:
    n = len(poly)
    tans: List[Point] = []
    for i in range(n):
        if i == 0:
            t = sub(poly[1], poly[0])
        elif i == n - 1:
            t = sub(poly[-1], poly[-2])
        else:
            t = sub(poly[i + 1], poly[i - 1])
        tans.append(normalize(t))
    return tans


def stroke(centerline: Sequence[Point], half_widths: Sequence[float],
           round_caps: bool = True, cap_steps: int = 8) -> List[Point]:
    """Offset a centerline by per-point half-widths into one closed contour.

    Produces left side forward + (optional end cap) + right side backward +
    (optional start cap). half_widths is the half stroke width at each point,
    letting callers modulate thickness for a broad-nib calligraphic look.
    """
    poly = [(float(x), float(y)) for (x, y) in centerline]
    n = len(poly)
    if n < 2:
        return []
    tans = _tangents(poly)
    left: List[Point] = []
    right: List[Point] = []
    for i in range(n):
        t = tans[i]
        nrm = (-t[1], t[0])  # left-hand normal
        hw = half_widths[i]
        left.append(add(poly[i], mul(nrm, hw)))
        right.append(add(poly[i], mul(nrm, -hw)))

    contour: List[Point] = list(left)

    if round_caps:
        contour += _cap(poly[-1], tans[-1], half_widths[-1], cap_steps, end=True)
    contour += list(reversed(right))
    if round_caps:
        contour += _cap(poly[0], tans[0], half_widths[0], cap_steps, end=False)
    return contour


def _cap(center: Point, tangent: Point, hw: float, steps: int, end: bool) -> List[Point]:
    """Semicircular cap bulging outward (forward at the end, backward at start)."""
    if hw <= 0:
        return []
    t = tangent if end else mul(tangent, -1.0)
    nrm = (-t[1], t[0])
    pts: List[Point] = []
    # Sweep from +90deg (left side) through 0 (outward bulge) to -90deg (right side).
    for s in range(1, steps):
        a = math.pi / 2 - math.pi * (s / steps)
        off = add(mul(nrm, hw * math.cos(a)), mul(t, hw * math.sin(a)))
        pts.append(add(center, off))
    return pts


def disc(center: Point, radius: float, steps: int = 24) -> List[Point]:
    """A filled circle contour."""
    cx, cy = center
    return [
        (cx + radius * math.cos(2 * math.pi * k / steps),
         cy + radius * math.sin(2 * math.pi * k / steps))
        for k in range(steps)
    ]
