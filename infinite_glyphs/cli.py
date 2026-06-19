#!/usr/bin/env python3
"""infinite-glyphs CLI: render and bake glyphs for arbitrarily large numeral bases.

Examples:
  # one glyph to SVG and PNG
  python cli.py glyph 666 --svg g.svg --png g.png

  # a contact sheet of a value range
  python cli.py sheet --start 62 --count 48 --out sheet.png

  # a whole number in a base (digits >=62 become cursive glyphs)
  python cli.py number 12345678901234 --base 666 --png number.png

  # bake an installable font covering every digit of a base
  python cli.py bake --base 666 --out InfiniteGlyphs-base666.ttf

  # show how a number decomposes (digits + font code-point string)
  python cli.py encode 12345678901234 --base 666
"""
from __future__ import annotations

import argparse
import os
import sys

from infinite_glyphs.glyphgen.metrics import DEFAULT
from infinite_glyphs.glyphgen.alphabet import to_digits
from infinite_glyphs.glyphgen.engine import glyph_outline
from infinite_glyphs.glyphgen import provider
from infinite_glyphs.render import svg as svg_backend


def _save_glyph(gly, svg_path, png_path, size):
    if svg_path:
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_backend.glyph_svg(gly))
        print(f"wrote {svg_path}")
    if png_path:
        from infinite_glyphs.render.png import glyph_image
        glyph_image(gly, size=size).save(png_path)
        print(f"wrote {png_path}")
    if not svg_path and not png_path:
        bb = gly.bbox()
        print(f"value {gly.value} [{gly.regime}]: {len(gly.contours)} contours, "
              f"{gly.point_count()} points, advance {gly.advance_width}, bbox {bb}")


def cmd_glyph(args):
    gly = glyph_outline(args.value)
    _save_glyph(gly, args.svg, args.png, args.size)
    return 0


def cmd_sheet(args):
    from infinite_glyphs.render.png import contact_sheet
    values = range(args.start, args.start + args.count)
    glyphs = [glyph_outline(v) for v in values]
    out = args.out or "sheet.png"
    contact_sheet(glyphs, cols=args.cols).save(out)
    print(f"wrote {out}  ({len(glyphs)} glyphs)")
    return 0


def cmd_number(args):
    specs = provider.glyphs_for_number(
        args.value, args.base, all_procedural=args.all_procedural)
    digits = to_digits(args.value, args.base)
    print(f"{args.value} in base {args.base} = {len(digits)} digits: {digits}")
    out = args.png or args.svg
    if not out:
        print("(use --png or --svg to render)")
        return 0
    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as f:
            f.write(svg_backend.number_svg(specs))
        print(f"wrote {args.svg}")
    if args.png:
        from infinite_glyphs.render.png import render_number
        render_number(specs).save(args.png)
        print(f"wrote {args.png}")
    return 0


def cmd_bake(args):
    from infinite_glyphs.font.bake import bake_font
    out = args.out or f"InfiniteGlyphs-base{args.base}.ttf"
    bake_font(range(args.base), family=args.family,
              unicode_base=int(args.unicode_base, 0), filepath=out)
    print(f"wrote {out}  ({os.path.getsize(out):,} bytes, {args.base} glyphs)")
    print(f"glyph for digit d is at code point {args.unicode_base} + d")
    return 0


def cmd_encode(args):
    from infinite_glyphs.font.bake import encode_number, PUA_BMP_BASE
    digits = to_digits(args.value, args.base)
    base_cp = int(args.unicode_base, 0)
    s = encode_number(digits, base_cp)
    print(f"{args.value} in base {args.base}:")
    print(f"  digits      : {digits}")
    print(f"  code points : {[hex(base_cp + d) for d in digits]}")
    print(f"  string      : {s!r}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="infinite-glyphs", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("glyph", help="render a single glyph for a value")
    g.add_argument("value", type=int)
    g.add_argument("--svg")
    g.add_argument("--png")
    g.add_argument("--size", type=int, default=200)
    g.set_defaults(func=cmd_glyph)

    s = sub.add_parser("sheet", help="contact sheet of a value range")
    s.add_argument("--start", type=int, default=62)
    s.add_argument("--count", type=int, default=48)
    s.add_argument("--cols", type=int, default=8)
    s.add_argument("--out")
    s.set_defaults(func=cmd_sheet)

    n = sub.add_parser("number", help="render a full number in a base")
    n.add_argument("value", type=int)
    n.add_argument("--base", type=int, required=True)
    n.add_argument("--svg")
    n.add_argument("--png")
    n.add_argument("--all-procedural", action="store_true",
                   help="generate glyphs even for small (conventional) digits")
    n.set_defaults(func=cmd_number)

    b = sub.add_parser("bake", help="bake an installable TTF for a base")
    b.add_argument("--base", type=int, required=True)
    b.add_argument("--out")
    b.add_argument("--family", default="Infinite Glyphs Cursive")
    b.add_argument("--unicode-base", default="0xE000",
                   help="code point for digit 0 (default 0xE000, the PUA)")
    b.set_defaults(func=cmd_bake)

    e = sub.add_parser("encode", help="show digit decomposition + code points")
    e.add_argument("value", type=int)
    e.add_argument("--base", type=int, required=True)
    e.add_argument("--unicode-base", default="0xE000")
    e.set_defaults(func=cmd_encode)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
