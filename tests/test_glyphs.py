"""Tests for the infinite-glyphs engine, regimes, renderers, and font baking."""
import xml.etree.ElementTree as ET

import pytest

from infinite_glyphs.glyphgen.alphabet import to_digits, conventional_char, CONVENTIONAL_SIZE
from infinite_glyphs.glyphgen.engine import glyph_outline
from infinite_glyphs.glyphgen import datamatrix, provider
from infinite_glyphs.glyphgen.provider import Conventional
from infinite_glyphs.glyphgen.outline import GlyphOutline


# --- base / digit decomposition -------------------------------------------

@pytest.mark.parametrize("value,base", [(0, 2), (666, 666), (12345678901234, 666),
                                        (255, 16), (1000000, 7)])
def test_to_digits_roundtrip(value, base):
    digits = to_digits(value, base)
    restored = 0
    for d in digits:
        assert 0 <= d < base
        restored = restored * base + d
    assert restored == value


def test_to_digits_zero():
    assert to_digits(0, 10) == [0]


def test_conventional_hex_first_16():
    assert "".join(conventional_char(d) for d in range(16)) == "0123456789abcdef"


# --- script engine: determinism + distinctness ----------------------------

def _sig(g: GlyphOutline):
    return tuple(tuple((round(x, 2), round(y, 2)) for x, y in c) for c in g.contours)


def test_engine_deterministic():
    for v in (62, 666, 99999):
        assert _sig(glyph_outline(v)) == _sig(glyph_outline(v))


def test_engine_distinct_over_range():
    sigs = {_sig(glyph_outline(v)) for v in range(62, 462)}
    assert len(sigs) == 400  # all 400 glyphs distinct


def test_engine_always_inks_something():
    for v in range(62, 200):
        g = glyph_outline(v)
        assert g.contours and g.point_count() > 0


def test_engine_advance_positive():
    g = glyph_outline(123)
    assert g.advance_width > 0


# --- data-matrix regime: scaling + uniqueness -----------------------------

def test_datamatrix_grid_grows_with_bits():
    small = datamatrix.grid_side_for(0xFF)         # 8 bits
    big = datamatrix.grid_side_for(1 << 99999)     # ~100k bits
    assert small < big
    assert big >= 317  # ceil(sqrt(99999))


def test_datamatrix_encodes_value_uniquely():
    a = datamatrix.datamatrix_outline(2 ** 64 + 1)
    b = datamatrix.datamatrix_outline(2 ** 64 + 2)
    assert _sig(a) != _sig(b)


def test_datamatrix_huge_value_builds():
    g = datamatrix.datamatrix_outline(2 ** 4096 + 7)
    assert g.regime == "datamatrix"
    assert g.contours


# --- provider: regime selection -------------------------------------------

def test_provider_small_is_conventional():
    spec = provider.glyph_for(10)
    assert isinstance(spec, Conventional)
    assert spec.char == "a"


def test_provider_mid_is_script():
    spec = provider.glyph_for(500)
    assert isinstance(spec, GlyphOutline)
    assert spec.regime == "script"


def test_provider_huge_is_datamatrix():
    spec = provider.glyph_for(10 ** 12, script_limit=1000)
    assert isinstance(spec, GlyphOutline)
    assert spec.regime == "datamatrix"


def test_provider_all_procedural_skips_conventional():
    spec = provider.glyph_for(10, all_procedural=True)
    assert isinstance(spec, GlyphOutline)


def test_glyphs_for_number_digit_count():
    specs = provider.glyphs_for_number(12345678901234, 666)
    assert len(specs) == len(to_digits(12345678901234, 666))


# --- SVG backend ----------------------------------------------------------

def test_glyph_svg_is_wellformed_xml():
    from infinite_glyphs.render.svg import glyph_svg
    root = ET.fromstring(glyph_svg(glyph_outline(666)))
    assert root.tag.endswith("svg")


def test_number_svg_is_wellformed_xml():
    from infinite_glyphs.render.svg import number_svg
    specs = provider.glyphs_for_number(98765, 666)
    root = ET.fromstring(number_svg(specs))
    assert root.tag.endswith("svg")


# --- font baking ----------------------------------------------------------

def test_bake_font_glyph_and_cmap_counts(tmp_path):
    from infinite_glyphs.font.bake import bake_font
    from fontTools.ttLib import TTFont
    out = tmp_path / "test.ttf"
    n = 100
    bake_font(range(n), filepath=str(out))
    f = TTFont(str(out))
    assert f["maxp"].numGlyphs == n + 1          # + .notdef
    assert len(f.getBestCmap()) == n


def test_bake_font_codepoint_mapping(tmp_path):
    from infinite_glyphs.font.bake import bake_font, PUA_BMP_BASE
    from fontTools.ttLib import TTFont
    out = tmp_path / "test.ttf"
    bake_font(range(20), filepath=str(out))
    cmap = TTFont(str(out)).getBestCmap()
    assert cmap[PUA_BMP_BASE + 0] == "g0"
    assert cmap[PUA_BMP_BASE + 19] == "g19"


def test_bake_font_rejects_overflow():
    from infinite_glyphs.font.bake import bake_font, MAX_GLYPHS_PER_FONT
    with pytest.raises(ValueError):
        bake_font(range(MAX_GLYPHS_PER_FONT + 5))
