# APCA-W3 algorithm reference

This document explains how APCA computes its `Lc` score, why the algorithm exists, and what each constant means. Read this before tweaking the script or before defending a finding to a stakeholder who's used to WCAG 2.x ratios.

## Why APCA replaced WCAG 2.x

WCAG 2.x's contrast ratio (the `4.5:1`, `3:1`, `7:1` numbers) was defined in 2008 and has three structural problems that APCA was designed to fix:

1. **It uses a relative luminance ratio that overweights blue.** The `(L_lighter + 0.05) / (L_darker + 0.05)` formula gives the same ratio for `#000` on `#fff` as it does for many less-readable combinations involving blue, because the blue coefficient (0.0722) is far smaller than perception studies support.
2. **It is symmetric.** WCAG 2.x ratio doesn't distinguish dark-on-light from light-on-dark. APCA does — they are perceptually different and require different math.
3. **It ignores font size and weight.** WCAG 2.x has only two thresholds (`4.5:1` for normal text, `3:1` for "large text" defined as 18px regular or 14px bold). APCA acknowledges that perceived contrast varies continuously with size and weight, and provides a 25-row × 9-column lookup table mapping `Lc` → minimum size per weight.

APCA is the algorithm proposed for WCAG 3 (currently in draft) as the replacement for WCAG 2.x's `relativeLuminance` ratio.

## The signed Lc score

APCA returns a single number, **`Lc`**, in roughly the range **−108 to +108**.

- **Positive** = dark text on light background (BoW: "Black on White")
- **Negative** = light text on dark background (WoB: "White on Black")
- **Magnitude** = perceived contrast strength

The sign is meaningful: BoW and WoB are not symmetric in human perception, and APCA uses *different exponents* for each polarity. Don't strip the sign blindly. Reports should preserve it; conformance lookups use the absolute value.

## Algorithm steps (apca-w3 v0.1.9, constants `0.0.98G-4g`)

### 1. sRGB → APCA luminance Y

For each channel `c ∈ {R, G, B}` in 0–1 sRGB:

```
Y = 0.2126729 · R^2.4
  + 0.7151522 · G^2.4
  + 0.0721750 · B^2.4
```

Note: APCA uses a **single 2.4 exponent** for the entire channel, not the piecewise sRGB transfer function with its linear segment near zero. This is intentional — APCA's near-black handling is done separately by the soft black clamp (step 2), not the gamma decode. This is one of the most common "bugs" in third-party APCA reimplementations: applying the standard sRGB EOTF here produces subtly wrong results.

### 2. Soft black clamp

For both `Y_text` and `Y_bg`:

```
if Y < 0.022:   Y = Y + (0.022 - Y)^1.414
```

Below `Y = 0.022` (about RGB 30/255), human contrast perception flattens. The clamp prevents the algorithm from claiming infinite contrast against pure black.

### 3. Polarity-dependent SAPC

If `Y_bg > Y_text` (dark text on light bg, BoW):

```
SAPC = (Y_bg^0.56 − Y_text^0.57) · 1.14
Lc   = 0   if SAPC < 0.10
       (SAPC − 0.027) · 100  otherwise
```

If `Y_text > Y_bg` (light text on dark bg, WoB):

```
SAPC = (Y_bg^0.65 − Y_text^0.62) · 1.14
Lc   = 0   if SAPC > -0.10
       (SAPC + 0.027) · 100  otherwise
```

### 4. The constants

| Constant      | Value  | Role                                                   |
| ------------- | ------ | ------------------------------------------------------ |
| `mainTRC`     | 2.4    | Channel gamma decode exponent                          |
| `R/G/B coef`  | 0.2127 / 0.7152 / 0.0722 | Luminance weights (Rec.709 D65)      |
| `normBG`      | 0.56   | BoW background exponent                                |
| `normTXT`     | 0.57   | BoW text exponent                                      |
| `revBG`       | 0.65   | WoB background exponent                                |
| `revTXT`      | 0.62   | WoB text exponent                                      |
| `blkThrs`     | 0.022  | Soft black threshold                                   |
| `blkClmp`     | 1.414  | Black-clamp exponent (approximately √2)                |
| `loClip`      | 0.10   | Low-contrast clip floor                                |
| `loBoWoffset` | 0.027  | BoW low-contrast smoothing offset                      |
| `loWoBoffset` | 0.027  | WoB low-contrast smoothing offset                      |
| `scaleBoW`    | 1.14   | BoW gain                                               |
| `scaleWoB`    | 1.14   | WoB gain                                               |
| `deltaYmin`   | 0.0005 | Minimum |Y_bg − Y_text| to compute (else Lc = 0)      |

These are **frozen at G-4g (Feb 2021)** by the upstream maintainer (Andrew Somers). Any APCA implementation claiming these values produces identical Lc up to floating-point round-off. If you compare this skill's output to another tool and the numbers disagree by more than ~0.1, one of the implementations is wrong.

## What APCA does NOT do

- **It does not handle alpha.** The official spec says "alpha unsupported." This skill pre-composites in sRGB as a pragmatic extension, with a warning.
- **It does not target wide-gamut displays.** APCA-P3 is on the roadmap upstream but not released. Wide-gamut inputs to this skill are clamped to sRGB.
- **It is not symmetric to WCAG 2.x ratio.** There is no exact mapping. Approximate guides exist (`Lc 75 ≈ WCAG 4.5:1`), but the relationship is non-monotonic — a token can pass APCA and fail WCAG 2.x or vice versa, and that's by design, not a bug.
- **It is not a replacement for actual user testing.** APCA quantifies *predicted readability under typical viewing conditions*. Users with specific visual conditions may need additional consideration.

## Further reading

- [APCA documentation hub](https://git.apcacontrast.com/) — the canonical reference site.
- [Myndex/SAPC-APCA](https://github.com/Myndex/SAPC-APCA) — algorithm derivation and historical context.
- [Myndex/apca-w3](https://github.com/Myndex/apca-w3) — the npm-published reference implementation this skill ports.
