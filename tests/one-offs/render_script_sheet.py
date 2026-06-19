"""Render a contact sheet of regime-2 (script) glyphs for visual QA.

Usage: python tests/one-offs/render_script_sheet.py
Writes tests/one-offs/out/script_sheet.png
"""
import os
import sys

# make repo root importable when run from anywhere
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from infinite_glyphs.glyphgen.engine import glyph_outline
from infinite_glyphs.render.png import contact_sheet

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

# 48 glyphs starting where the conventional alphabet (62) leaves off,
# plus a few specific values of interest.
values = list(range(62, 62 + 40)) + [123, 456, 666, 665, 1000, 9001, 31337, 100000]
glyphs = [glyph_outline(v) for v in values]

sheet = contact_sheet(glyphs, cols=8, cell=150)
path = os.path.join(OUT, "script_sheet.png")
sheet.save(path)
print(f"wrote {path}  ({sheet.size[0]}x{sheet.size[1]})")

# determinism + distinctness quick check
import hashlib
def sig(g):
    return hashlib.md5(repr([[ (round(x,2),round(y,2)) for x,y in c] for c in g.contours]).encode()).hexdigest()
again = [glyph_outline(v) for v in values]
det = all(sig(a) == sig(b) for a, b in zip(glyphs, again))
distinct = len({sig(g) for g in glyphs}) == len(glyphs)
print(f"deterministic re-render: {det}")
print(f"all distinct: {distinct} ({len({sig(g) for g in glyphs})}/{len(glyphs)} unique)")
