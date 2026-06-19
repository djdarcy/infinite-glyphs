# infinite-glyphs

Procedural glyphs for **arbitrarily large numeral bases** — so a number written in
a base like `tri(36) = 666` (which needs 666 distinct single-character digits, far
beyond decimal or hex) can actually be rendered, typed, and printed.

Glyphs are generated on demand (truly unbounded), render to **SVG** and **PNG**, and
bake into an **installable TTF font**. The same number always produces the same
glyph, and different numbers always differ.

## Why

This grew out of [Prime-Square-Sum](https://github.com/djdarcy/Prime-Square-Sum)'s
`stf()` digit-triangle (e.g. `0123 + 456 + 78 + 9 = 666`). Reading a triangle of
`tri(n)` cells as digits in base `tri(n)` needs `tri(n)` unique single-glyph digits.
Decimal gives 10, hex 16, ASCII ~95 — nowhere near enough. infinite-glyphs makes
the digits on demand.

## Three regimes

A digit value is rendered by the regime that fits its size (auto-selected in
`glyphgen/provider.py`):

| Regime | Digit value | Glyph | Readable? |
|--------|-------------|-------|-----------|
| **Conventional** | `< 62` | real characters `0-9 a-z A-Z` (hex = first 16) | yes, familiar |
| **Script** | `62 .. ~1e6` | procedural calligraphic cursive mark | yes, tellable apart |
| **Data-matrix** | beyond that | dot grid that grows with bit-length | unique (maybe not perceptibly) |

The data-matrix regime is what makes "infinite" rigorous: visual uniqueness is
floored at `log2(N)` distinguishable cells, so the grid scales with the value's
bit-length (e.g. base `2^99999` needs a 317×317 grid).

## Install

```bash
git clone https://github.com/djdarcy/infinite-glyphs.git
cd infinite-glyphs
pip install -e ".[dev]"        # includes skia-pathops for clean font contours
```

Runtime deps: `Pillow`, `fonttools`. Recommended extra: `skia-pathops` (without it,
baked glyphs may render thin).

## Usage

```bash
# one glyph -> SVG and PNG
python -m infinite_glyphs glyph 666 --svg g.svg --png g.png

# a contact sheet of a value range (visual QA)
python -m infinite_glyphs sheet --start 62 --count 48 --out sheet.png

# a whole number in a base
python -m infinite_glyphs number 12345678901234 --base 666 --png number.png

# bake an installable font covering every digit of a base
python -m infinite_glyphs bake --base 666 --out InfiniteGlyphs-base666.ttf

# show how a number decomposes (digits + font code points)
python -m infinite_glyphs encode 12345678901234 --base 666
```

After installing the baked font, a number is the string of its code points (digit
`d` maps to `U+E000 + d` by default — see `encode`).

## How it works

- **Engine** (`glyphgen/engine.py`): an integer seeds a deterministic RNG that draws
  a broad-nib calligraphic stroke from a vocabulary of archetypes (bowls, stems,
  arches, waves, diagonals, ascender/descender loops), flattened to vector contours.
- **Render** (`render/`): SVG (`<path>`/`<text>`) and PNG (nonzero-winding scanline
  rasterizer, no system font needed).
- **Font** (`font/bake.py`): contours → TTF via `fontTools`, with `skia-pathops`
  overlap removal so strokes fill solid in real font engines.

A cellular-automata regime (`glyphgen/automata.py`) is scaffolded as an alternative
visual language for a future release.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
