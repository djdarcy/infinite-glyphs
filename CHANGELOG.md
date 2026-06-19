# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-19

Initial release: a working cursive glyph set, three regimes, and font baking.

### Added
- **Glyph engine** (`glyphgen/`): deterministic, distinct glyphs for any non-negative
  integer, with three auto-selected regimes:
  - conventional characters (`0-9 a-z A-Z`) for small digit values
  - procedural calligraphic **cursive** script from a stroke-archetype vocabulary
  - **data-matrix** dot grid that scales with bit-length for astronomically large bases
- **Provider** (`glyphgen/provider.py`): regime auto-selection + base/digit decomposition.
- **Rendering**: SVG (`render/svg.py`) and PNG (`render/png.py`, nonzero-winding raster).
- **Font baking** (`font/bake.py`): installable TTF via fontTools with skia-pathops
  overlap removal; code points map digit `d` to `U+E000 + d` by default.
- **CLI** (`infinite_glyphs/cli.py`): `glyph`, `sheet`, `number`, `bake`, `encode`.
- **Cellular-automata** generator (`glyphgen/automata.py`) scaffolded for a future
  alternative regime (not yet wired into the provider).
- Tests: 24 unit/integration tests (determinism, distinctness, regime selection,
  SVG validity, font glyph/cmap counts).

[Unreleased]: https://github.com/djdarcy/infinite-glyphs/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/djdarcy/infinite-glyphs/releases/tag/v0.1.0
