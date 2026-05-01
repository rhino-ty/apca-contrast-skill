# fontLookupAPCA matrix reference

The `fontMatrixAscend` table (in `scripts/_tables.py`) is the official APCA conformance lookup, ported verbatim from `Myndex/apca-w3@0.1.9`. This document explains how to read it, what each cell means, and when each variant applies.

## Purpose

Given an `Lc` score and a font weight, the table answers a single question:

> What is the **minimum body-text font size in CSS pixels** for which this contrast passes APCA?

This replaces WCAG 2.x's two crude thresholds (`4.5:1` / `3:1`) with a continuous lookup across 25 contrast levels and 9 weights — 225 cells in total.

## Table shape

- **Rows** (25): `Lc` levels in steps of 5, from 0 through 125
- **Columns** (9): font weights from 100 (Thin) through 900 (Black)
- **Cells**: minimum font size in px, OR a sentinel value (see below)

```
       Lc \ wt | 100  200  300  400  500  600  700  800  900
       ---------------------------------------------------------
        0      | 999  999  999  999  999  999  999  999  999
       15      | 777  777  777  777  777  777  777  777  777
       45      | 108   96   72   42   32   28   24   24   24
       75      |  60   42   24   18   16   15   14   16   18
       90      |  48   32   21   16  15.5 14.5  14   16   18
      105      |  39   25   18  14.5  14   13   12   16   18
```

## Sentinel values

| Cell value | Meaning                                                                           |
| ---------- | --------------------------------------------------------------------------------- |
| `999`      | **Absolute non-text** — contrast is so low the combo cannot be used at any size.   |
| `777`      | **Non-conformance** — any size at this Lc/weight fails. Effectively unusable.     |
| `0`        | **Not applicable** — only used to mark unused weight buckets at extreme rows.     |
| `> 0`      | Minimum px at weight ≥ 100, ≤ 900, for body text                                  |

The skill collapses `0`/`777`/`999` into a single "fail" verdict and reports the numeric minimum otherwise.

## How lookup works

1. Take `abs(Lc)` (the magnitude — sign indicates polarity but the table is symmetric on magnitude).
2. **Round down to the nearest 5** to get the row key. So `Lc = 73` and `Lc = 70` both hit the row labeled `Lc = 70`.
3. Find the column for the requested weight. If the weight isn't a multiple of 100, snap to the nearest valid weight.
4. The cell value is the minimum px for body text. If the user's font size ≥ cell value, the combo passes for that role.

Worked example: `Lc = 73, weight = 500`.

- Round down → row `Lc = 70`.
- Column → `500`.
- Cell → `18`. So this combination passes for body text at ≥18px @ 500wt.

## Why the cells are not monotonic across weights

Look at row `Lc 75`: `[60, 42, 24, 18, 16, 15, 14, 16, 18]`. The minimum size **goes back up** at weights 800–900. This is intentional — at very heavy weights, letterforms become so dense that perceived contrast drops slightly, requiring larger sizes to remain readable. The table reflects perception studies, not arithmetic interpolation. Don't "smooth" it.

Similarly, row `Lc 60` ends `[..., 16, 16, 18]` — same effect at the top end.

## Variants in upstream apca-w3

This skill ships only the **Ascend** variant (`fontMatrixAscend`), which is the most commonly applied and corresponds to the APCA Bronze conformance default for body text. The upstream library also exposes:

- `fontDeltaAscend` — derivative table for fine-grained interpolation (not used here)
- Other matrices for non-text UI roles (icons, borders), large headlines, and dynamic text

If you need any of these, open an issue. The omission is deliberate scope reduction: 95% of design-system audit questions are body-text questions, and the Ascend variant answers those correctly.

## Common edge cases

### "It says my Lc 75 / 14px @ 400 fails — but I think it looks fine."

Look at row `Lc 75`, column `400`: minimum is `18`. So 14px @ 400 fails — that's correct per the table. APCA's stance is that 14px regular needs roughly Lc 90 to be comfortable. Either:

- Bump the size to 16–18px,
- Bump the weight to 500+ (`Lc 75 / 14px @ 500` requires only 16px → close to passing), or
- Bump the contrast (target Lc ≥ 90).

### "Two adjacent Lc rows give wildly different mins."

That's expected near the steep parts of the curve (around Lc 30–45). The table is a discrete approximation of a continuously-varying surface; rounding down to the nearest 5 means you can land on a "harder" row by 1–2 Lc points. If your finding is right on the boundary, the recommendation is conservative: round to the harder side and tighten the design.

### "I have weight 450 (variable font)."

Variable font weights aren't in the standard 100/200/.../900 grid. The skill snaps to the nearest, but for design-system audits the conservative move is to test at the nearest valid weight *below* the actual (e.g. test 450 as 400). This errs on the side of safety.

## Reproducing

If you want to verify this skill's table matches upstream, fetch:

```
https://raw.githubusercontent.com/Myndex/apca-w3/master/src/apca-w3.js
```

The arrays in `_tables.py` are byte-for-byte identical to that file's `fontMatrixAscend`. Any divergence is a bug in this skill — please open an issue with both tables side-by-side.
