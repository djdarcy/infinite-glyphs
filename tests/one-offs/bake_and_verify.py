"""Bake a base-666 cursive font and verify it renders through FreeType.

Writes tests/one-offs/out/InfiniteGlyphs-base666.ttf and a proof PNG rendered
by Pillow's FreeType engine (i.e. the same path any app would use).
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from infinite_glyphs.font.bake import bake_font, encode_number, PUA_BMP_BASE
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)
ttf = os.path.join(OUT, "InfiniteGlyphs-base666.ttf")

BASE = 666
bake_font(range(BASE), family="Infinite Glyphs Cursive", filepath=ttf)
print(f"baked {ttf}  ({os.path.getsize(ttf):,} bytes)")

# 1) structural check: reopen with fontTools
f = TTFont(ttf)
print("numGlyphs:", f["maxp"].numGlyphs)
print("cmap entries:", len(f.getBestCmap()))
print("sample cmap:", {hex(k): v for k, v in list(f.getBestCmap().items())[:4]})

# 2) end-to-end render via FreeType (Pillow) -- proves it's installable/usable
sample_digits = [3, 17, 40, 62, 123, 400, 500, 665]
text = encode_number(sample_digits, PUA_BMP_BASE)
pilfont = ImageFont.truetype(ttf, 120)
img = Image.new("L", (1400, 240), 255)
d = ImageDraw.Draw(img)
d.text((30, 40), text, fill=0, font=pilfont)
png = os.path.join(OUT, "font_render.png")
img.save(png)
print(f"wrote {png}  (digits {sample_digits} rendered FROM the baked font)")
