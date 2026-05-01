# Changelog

All notable changes to this skill are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The APCA core algorithm (`apca-w3@0.1.9`, constants `0.0.98G-4g`) is frozen
upstream, so most changes here will be about the skill's surrounding tooling
(parsers, extractors, output formats) rather than the math.

## [1.0.0] — 2026-05-01

### Added

- APCA-W3 v0.1.9 core algorithm (`apca_lc`) with constants frozen at `0.0.98G-4g`.
- Official `fontMatrixAscend` lookup table from `Myndex/apca-w3@0.1.9`, ported verbatim.
- 8 CSS color notations:
  - Hex (3/4/6/8 digit forms)
  - `rgb()` / `rgba()` (legacy comma and modern space-separated)
  - `hsl()` / `hsla()` (with deg/rad/turn hue units)
  - `oklch()` / `oklab()` (CSS Color Module Level 4)
  - `color()` with `srgb`, `srgb-linear`, `display-p3`, `rec2020` color spaces
  - 148 named colors (CSS Color Module Level 4, including `rebeccapurple` and `transparent`)
- `--from-tailwind` mode: auto-extracts `:root` and `.dark` blocks from Tailwind v4 `globals.css` and audits all common semantic tokens (`foreground`, `muted-foreground`, `primary`, `secondary-foreground`, `accent-foreground`, `destructive`, `card-foreground`, `popover-foreground`, `border`) side-by-side against `--background` (or override with `--bg-token`).
- `--batch` mode supporting two input shapes (explicit pairs list, or shared-background tokens map).
- `--reverse` mode: binary-search a neutral-grey foreground that hits a target |Lc| on a given background.
- `--matrix` flag: render the size×weight pass/fail grid for typical body sizes (12/14/16/18/24/32 px) × weights (400/500/600/700).
- `--json` flag for machine-readable output across all modes.
- Alpha compositing (foreground over background in sRGB) with explicit `⚠ unofficial` warning per APCA spec.
- Wide-gamut → sRGB conversion (Display-P3, Rec.2020) via D65 matrices, clamped to sRGB gamut.
- `examples/sample-globals.css` (shadcn Neutral default theme), `examples/sample-batch.json`, and a worked `examples/sample-audit-report.md`.
- `references/APCA-ALGORITHM.md` and `references/FONT-LOOKUP-TABLE.md` deep-reference docs.

### Notes

- This is the first public release. Algorithm output is byte-for-byte identical to `Myndex/apca-w3@0.1.9` for any input both implementations accept (modulo float round-off in the last decimal of Lc).
- Python stdlib only — no `pip install` required.

[1.0.0]: https://github.com/rhino-ty/apca-contrast-skill/releases/tag/v1.0.0
