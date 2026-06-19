"""Render a real multi-digit number in a large base, cursive style.

Shows the payoff: a number written in base tri(36)=666, where digit values
0..61 are familiar characters and 62..665 are generated cursive glyphs.
Writes tests/one-offs/out/number_demo.png
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from infinite_glyphs.glyphgen.alphabet import to_digits
from infinite_glyphs.glyphgen.provider import glyphs_for_number, Conventional
from infinite_glyphs.render.png import render_number
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

BASE = 666  # tri(36)
value = 12_345_678_901_234

digits = to_digits(value, BASE)
print(f"value {value} in base {BASE} = {len(digits)} digits: {digits}")

# default provider: digits <62 are real chars, >=62 are cursive glyphs
specs_mixed = glyphs_for_number(value, BASE)
mixed = render_number(specs_mixed)

# all-procedural: every digit becomes a cursive glyph (self-contained script)
specs_all = glyphs_for_number(value, BASE, all_procedural=True)
allproc = render_number(specs_all)

# stack the two strips with labels
W = max(mixed.width, allproc.width)
sheet = Image.new("L", (W, mixed.height + allproc.height + 10), 255)
sheet.paste(mixed, (0, 0))
sheet.paste(allproc, (0, mixed.height + 10))
path = os.path.join(OUT, "number_demo.png")
sheet.save(path)
print(f"wrote {path}  ({sheet.size[0]}x{sheet.size[1]})")
print("top strip  = mixed (real chars + cursive),  bottom strip = all-procedural cursive")
