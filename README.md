# apca-contrast-skill

> Claude Code skill: APCA-W3 v0.1.9 perceptual contrast measurement with the official `fontLookupAPCA` pass/fail table — design system audits for Tailwind v4 / shadcn oklch tokens, light/dark mode side-by-side, every CSS color notation.

[![Made with](https://img.shields.io/badge/Made%20with-Claude%20Skills-blueviolet)](https://docs.claude.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![APCA-W3](https://img.shields.io/badge/APCA--W3-v0.1.9-green)](https://github.com/Myndex/apca-w3)

---

Stop regenerating contrast math at runtime. This skill bundles a deterministic Python script (stdlib only) that gives Claude Code a reliable way to:

- Measure APCA Lc for any text/background pair in **8 color notations**
- Look up the **exact minimum font size and weight** that passes (using the verbatim `fontMatrixAscend` table from `apca-w3@0.1.9`)
- Audit a Tailwind v4 `globals.css` end-to-end — extracts `:root` and `.dark` blocks and reports every common semantic token side-by-side
- Reverse-solve a color: "what shade do I need for Lc 75 on this background?"

Built because asking an LLM to rewrite the APCA algorithm on every contrast question is wasteful and inconsistent. The math is deterministic; bundle it once.

## Why APCA, not WCAG 2.x ratio

WCAG 2.x's contrast ratio is mathematically broken for modern displays — it overweights blue, treats dark-on-light and light-on-dark identically, and gives demonstrably wrong results for both extremes. APCA (Accessible Perceptual Contrast Algorithm) is the perceptually-uniform successor that replaces it in WCAG 3 draft. This skill implements **APCA-W3 v0.1.9** with constants frozen at `0.0.98G-4g` (verified current as of 2026).

## Install

Clone into your Claude Code user-level skills directory:

```bash
git clone https://github.com/rhino-ty/apca-contrast-skill.git \
  ~/.claude/skills/apca-contrast
```

That's it. The skill auto-loads on the next Claude Code session and triggers when you ask about contrast, Lc, accessibility, design tokens, etc.

To verify:

```bash
python3 ~/.claude/skills/apca-contrast/scripts/apca.py "#000" "#fff"
# Lc: +106.0 (BoW)
# Verdict: Pass — body minimum ≥14.5px @ 400wt
```

Or run the bundled shadcn/ui Neutral-theme example to see what a full audit looks like:

```bash
python3 ~/.claude/skills/apca-contrast/scripts/apca.py \
  --from-tailwind ~/.claude/skills/apca-contrast/examples/sample-globals.css
```

The corresponding worked-out report — including the dark-mode `destructive` failure that ships in the shadcn default — is in [`examples/sample-audit-report.md`](examples/sample-audit-report.md).

## Usage from Claude Code

Just ask in natural language. Example triggers:

- "이 디자인 시스템 토큰들 대비 봐줘" / "audit this design system"
- "muted-foreground가 14px medium에서 통과해?"
- "다크 모드 destructive 토큰 가독성 어때?"
- "white 배경에 Lc 75 통과하는 회색 추천해줘"

Or invoke the script directly:

```bash
SCRIPT=~/.claude/skills/apca-contrast/scripts/apca.py

# 1. Single pair
python3 $SCRIPT "#737373" "#fff"

# 2. Tailwind v4 audit (light + dark side-by-side)
python3 $SCRIPT --from-tailwind path/to/globals.css

# 3. Batch from JSON
python3 $SCRIPT --batch pairs.json

# 4. Reverse APCA — find a color that hits target Lc
python3 $SCRIPT --reverse "white" 75
# → use #6f6f6f (actual Lc +74.8)

# 5. Full size×weight matrix
python3 $SCRIPT --matrix "oklch(0.5 0.1 200)" "oklch(1 0 0)"

# Add --json to any command for structured output
```

## What you get

For each pair, the script returns:

- **Signed Lc** (positive = dark text on light bg, negative = inverse)
- **Polarity** (BoW / WoB)
- **Verdict** keyed at weight 400
- **Minimum font size per weight** (400, 500, 600, 700) — pulled from the official `fontMatrixAscend`
- Optional **size × weight pass/fail matrix** for typical body sizes
- Composed sRGB hex when alpha compositing was applied

For `--from-tailwind`, you additionally get:

- Both `:root` (light) and `.dark` blocks parsed automatically
- Every common semantic token (`foreground`, `muted-foreground`, `primary`, `secondary-foreground`, `accent-foreground`, `destructive`, `card-foreground`, `popover-foreground`, `border`) audited against `--background` (or override with `--bg-token`)
- Light/dark side-by-side report — designed to surface mode asymmetries (the most common design-system bug)

## Color notations supported

| Format          | Examples                                              |
| --------------- | ----------------------------------------------------- |
| Hex             | `#fff`, `#ffffff`, `#fff8`, `#ffffff80`               |
| `rgb` / `rgba`  | `rgb(255 255 255)`, `rgba(0,0,0,0.5)`, `rgb(100% 0 0)`|
| `hsl` / `hsla`  | `hsl(0 0% 50%)`, `hsla(120, 100%, 25%, 0.5)`          |
| `oklch`         | `oklch(0.205 0 0)`, `oklch(50% 0.1 200deg)`           |
| `oklab`         | `oklab(0.5 0.05 -0.1)`                                |
| `color()` sRGB  | `color(srgb 1 0 0)`, `color(srgb-linear 0.5 0.5 0.5)` |
| `color()` P3    | `color(display-p3 1 0 0)` (auto-clamps to sRGB gamut) |
| `color()` 2020  | `color(rec2020 1 0 0)` (auto-clamps to sRGB gamut)    |
| Named           | `red`, `white`, `rebeccapurple`, `transparent`, ...   |

148 CSS named colors (CSS Color Module Level 4) including `rebeccapurple`. Wide-gamut inputs (Display-P3, Rec.2020) are converted via D65 matrices and clamped to sRGB — appropriate because APCA targets sRGB displays.

## Reverse APCA — solve for a color

Given a background and a target Lc, find a neutral grey foreground that hits it:

```bash
python3 scripts/apca.py --reverse "white" 75
# For bg white, target |Lc|=75: use #6f6f6f (actual Lc +74.8)

python3 scripts/apca.py --reverse "#1a1a1a" 90
# For bg #1a1a1a, target |Lc|=90: use #e5e5e5 (actual Lc -89.7)
```

Useful when you know what Lc you need (e.g. "Lc 75 for body text 16px @ 400") and need a starting shade to plug into your token system.

## Limitations

Two kinds of limits — what **APCA itself** cannot tell you (true of every APCA tool, including the upstream library), and what **this specific implementation** doesn't yet handle. Knowing the difference matters: don't blame the script for things the algorithm can't do.

### APCA itself — what no APCA tool can tell you

- **WCAG 3 draft, not adopted.** APCA is the proposed contrast model for WCAG 3, which has been in draft since 2021 with no fixed adoption date. **Legal compliance regimes (ADA, EN 301 549, KWCAG, Section 508) all still mandate WCAG 2.x AA.** Passing APCA does *not* protect you from a WCAG 2.x-based complaint. For production audits you need both: APCA for design quality, WCAG 2.x ratio for legal cover. This skill does NOT compute WCAG 2.x ratio — pair it with a WCAG 2.x checker for compliance work.
- **Algorithm frozen since Feb 2021.** Constants are at `0.0.98G-4g`. Stability is good for reproducibility, but it also means HDR, OLED sub-pixel light bleed, and new display tech aren't reflected.
- **Single perceptual model.** APCA assumes one "average user, average sRGB display, average office lighting." Color blindness, low vision, age-related vision changes, and viewing in bright sun or dim rooms aren't differentiated. Real accessibility audits need additional vision-condition checks (e.g. deuteranopia/protanopia simulation).
- **Lc 0–30 is the noisy zone.** Below Lc ~30, the underlying perceptual model loses fidelity. Findings in that range are directionally right ("this is bad") but the exact number isn't precise.
- **Font family and rendering are ignored.** Pretendard at 14px and Times New Roman at 14px are *not* equally readable, but APCA treats them identically. Same for macOS subpixel rendering vs Windows ClearType vs mobile Roboto. The size thresholds in `fontMatrixAscend` are a good *starting point*, not the full story.
- **Variable-font weights aren't first-class.** APCA only knows the 100/200/.../900 grid. A weight of 450 (legitimate in variable fonts) gets snapped — conservative, but imprecise.
- **sRGB only.** APCA-P3 is on the upstream roadmap but unreleased. If your real users are on P3-native displays (most modern phones, MacBooks since 2016), the actual on-screen contrast may differ slightly from what APCA predicts.
- **Contrast is necessary, not sufficient.** Readability depends on contrast *plus* typography (line-height, tracking, x-height) *plus* layout. Lc 90 in a cramped 1.0 line-height paragraph is still hard to read. APCA can't tell you that.
- **Ecosystem maturity.** Figma, Adobe XD, browser DevTools, and most accessibility test suites still use WCAG 2.x ratio by default. If you adopt APCA internally, expect onboarding cost — "Lc 75" isn't intuitive the way "4.5:1" pretends to be.

### This implementation — additional caveats

- **Alpha compositing is not part of the APCA spec.** The script pre-composites foreground over background in sRGB (the pragmatic approach most tools take), but the official APCA position is "alpha is unsupported." When alpha is involved, the output includes a `⚠ Alpha compositing applied (unofficial)` warning. For surfaces with arbitrary content behind a translucent layer (image hero with text overlay, etc.), this approximation can be wrong by 5–10 Lc.
- **Only the `Ascend` variant of `fontLookupAPCA` is bundled.** Bronze conformance has multiple sub-tables for different roles (body, headlines, non-text UI). Ascend covers ~95% of body-text audit questions. If you need other variants, open an issue.
- **Lc lookup rounds down to the nearest 5.** Lc 73 and Lc 70 hit the same row. When findings are right on a boundary, the verdict is conservative — call this out in reports.
- **Tailwind extractor catches direct values only.** `var(--other)` chained references are not resolved. Inline the actual color first, or run the extractor against your *built* CSS (post-Tailwind), not the source.
- **No CSS-in-JS / `@theme inline` token rewriting.** Reads raw `:root` / `.dark` blocks. Point it at the file Tailwind ultimately emits to the browser.
- **Wide-gamut inputs clamp to sRGB.** `color(display-p3 1 0 0)` becomes `#ff0000` after clamp, which loses the actual P3 saturation. Output Lc reflects what an sRGB display would show, not what a P3 display would show. APCA-P3 (when it ships) will fix this; until then, treat P3 inputs as a sRGB approximation.

## When NOT to rely on this skill alone

- **Legal accessibility audits (ADA, KWCAG, EN 301 549, Section 508).** Run a WCAG 2.x ratio checker alongside. APCA pass + WCAG 2.x AA pass is the safe combination.
- **Audits for users with specific vision conditions.** APCA averages. For projects with known low-vision audiences (e.g. medical software, elder care), use vision-simulation tools in addition.
- **Hi-fi typography evaluation.** APCA is one of three legs (contrast + typography + layout). Use this skill for the contrast leg, not as the whole audit.
- **HDR / wide-gamut design pipelines.** Until APCA-P3 ships, this skill gives you a sRGB-equivalent answer, not a true wide-gamut answer.

## Algorithm provenance

The APCA core (`apca_lc`) and `fontMatrixAscend` table are both ported verbatim from [`Myndex/apca-w3@0.1.9`](https://github.com/Myndex/apca-w3) (the canonical W3-licensed implementation). Constants are frozen at `0.0.98G-4g` per the upstream maintainer's stability commitment.

If you want to know exactly *why* APCA exists and how it differs from WCAG 2.x ratio, the bundled deep-dives go further than most public docs:

- [`references/APCA-ALGORITHM.md`](references/APCA-ALGORITHM.md) — the math, every constant explained, common reimplementation bugs, and what APCA does *not* do.
- [`references/FONT-LOOKUP-TABLE.md`](references/FONT-LOOKUP-TABLE.md) — how to read `fontMatrixAscend`, why the cells aren't monotonic, sentinel values (999/777/0), and lookup edge cases.

Upstream / external references:

- [APCA documentation hub](https://git.apcacontrast.com/)
- [The original SAPC-APCA repo](https://github.com/Myndex/SAPC-APCA)
- [The Bronze Simple conformance table](http://apcaw3.myndex.com/)

## Repository layout

```
apca-contrast-skill/
├── SKILL.md             # Claude Code skill manifest (frontmatter + body)
├── scripts/
│   ├── apca.py          # Main CLI entry point (parsers, APCA core, modes)
│   └── _tables.py       # fontMatrixAscend, named colors, gamut matrices
├── examples/
│   ├── sample-globals.css       # shadcn/ui Neutral default theme
│   ├── sample-batch.json        # mixed-format batch input
│   └── sample-audit-report.md   # worked-out audit with real findings
├── references/
│   ├── APCA-ALGORITHM.md        # algorithm deep-dive
│   └── FONT-LOOKUP-TABLE.md     # lookup table semantics
├── CHANGELOG.md         # versioned change history
├── LICENSE              # MIT
└── NOTICE               # third-party attribution
```

Version history is in [CHANGELOG.md](CHANGELOG.md).

## Why this exists

Without this skill, an AI assistant that wants to check contrast either:

1. **Re-implements APCA from memory** every time — wasteful, slow, and prone to subtle bugs (esp. the soft black clamp and offset constants).
2. **Hand-waves WCAG 2.x ratio** — wrong answer, but at least small and consistent.
3. **Refuses to answer** — unhelpful.

This skill makes option 4 — "use the deterministic, official-table-backed implementation" — the cheap default.

## License

MIT — see [LICENSE](LICENSE). Third-party attribution for the APCA constants and `fontMatrixAscend` table (derived from `Myndex/apca-w3`) is recorded in [NOTICE](NOTICE).

## Contributing

Issues and PRs welcome. Areas of interest:

- Additional `fontLookupAPCA` variants (non-body roles)
- Resolving `var(--token)` chains in the Tailwind extractor
- Other framework extractors (CSS-in-JS, vanilla extract, Style Dictionary)
- Wide-gamut display targets (when APCA-P3 lands)

## Related skills

- [polymedia-review-skill](https://github.com/rhino-ty/polymedia-review-skill) — Socratic-maieutic review notes for books / games / movies / music (Obsidian)
- [review-myblog-converter](https://github.com/rhino-ty/review-myblog-converter) — convert Obsidian review notes into Naver Blog / Tistory / Velog tone (companion to polymedia-review-skill)
- [game-architect](https://github.com/rhino-ty/game-architect) — end-to-end indie game design (mechanics, balancing, GDD, narrative, marketing)
- [k-law-assistant](https://github.com/rhino-ty/k-law-assistant) — real-time Korean law lookup via Beopmang API
- [web-project-plan](https://github.com/rhino-ty/web-project-plan) — structured interview to scaffold new app projects

See [cc-system](https://github.com/rhino-ty/cc-system) for the full collection of my Claude Code agents and skills.
