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

A short list of every APCA tool's blind spots — not just this implementation's. Knowing these protects you from over-claiming what an APCA pass means.

### Standards / legal

- **APCA is a WCAG 3 *draft*, not law.** WCAG 3 has been in draft since 2021 with no fixed adoption date. Every accessibility legal regime in force today (ADA, Section 508, EN 301 549, KWCAG, AODA) **mandates WCAG 2.x AA**, not APCA. Passing APCA does not satisfy any of these by itself. Production accessibility audits should pair APCA (for design quality) with a WCAG 2.x ratio check (for legal cover).
- **Symbolic mismatch with WCAG 2.x.** There is no exact `Lc → ratio` mapping. Approximate guides exist (`Lc 75 ≈ WCAG 4.5:1`), but the relationship is **non-monotonic** — a token can pass APCA and fail WCAG 2.x or vice versa. That's by design (the algorithms model contrast differently), not a bug.

### Algorithm scope

- **It does not handle alpha.** The official spec says "alpha unsupported." Compositing translucent foregrounds is left to the caller. This skill pre-composites in sRGB as a pragmatic extension, with a warning, but the result can be wrong by several Lc when the actual content behind the layer varies (hero images, video).
- **It does not target wide-gamut displays.** APCA-P3 is on the upstream roadmap but unreleased. APCA's prediction is for an sRGB-display viewing the input. On a P3-native display, real on-screen contrast may differ slightly. Inputs to this skill in `color(display-p3 ...)` or `color(rec2020 ...)` are clamped to sRGB before evaluation.
- **It does not model HDR or new display technologies.** The 2.4 gamma exponent, the soft-black clamp, and the perceptual coefficients were tuned for SDR sRGB at typical office viewing conditions. HDR (PQ/HLG) content, OLED sub-pixel light bleed, and very-low-brightness modes (e-paper, transflective LCD) are out of scope.
- **Lc 0–30 is the noisy zone.** The perceptual model loses fidelity for very low contrasts. Findings in this range are directionally correct ("this fails") but the exact Lc shouldn't be quoted as precise.
- **The constants are frozen.** `0.0.98G-4g`, Feb 2021. No updates have shipped since. This is presented as a stability commitment by the upstream maintainer; whether you read it as "settled science" or "stagnation" is a judgment call. Either way, the algorithm doesn't track new evidence.

### Vision diversity

- **Single perceptual model.** APCA was tuned to predict readability for a single hypothetical "average user" — normal trichromatic vision, no significant impairment, average lighting. It does not differentiate:
  - Color blindness (deuteranopia, protanopia, tritanopia) — affects perceived contrast on red/green pairs especially
  - Low vision (cataract, macular degeneration, glaucoma) — affects required Lc thresholds substantially
  - Age-related changes (presbyopia, reduced retinal sensitivity) — typically requires +10–20 Lc above the average-user threshold
  - Cognitive disabilities (dyslexia) — readability depends on more than contrast (font, spacing, layout)
- **Single viewing condition.** Outdoor sunlight, dim evening, fluorescent office, OLED brightness mode all produce different effective contrast on the same token pair. APCA averages.

### Contrast is not readability

- **Typography matters as much as contrast.** Pretendard 14px is *more* readable than Times New Roman 14px at the same Lc, because of differences in x-height, stroke width, and counter shape. APCA treats them identically. The minimum px values from `fontMatrixAscend` should be treated as floors, not optima — the right *comfortable* size depends on the actual face.
- **Layout factors are out of scope.** Line-height, tracking, line length, paragraph spacing, surrounding visual noise, animation — all affect readability and none are inputs to APCA.
- **Variable-font weights aren't first-class.** APCA's table only knows the 100/200/.../900 grid. Variable-font weight 450 has no defined cell. This skill snaps to the nearest standard weight, which is conservative but imprecise for designs that deliberately use intermediate weights.
- **Font rendering varies by platform.** macOS subpixel rendering, Windows ClearType, Android system rendering, and various SVG/canvas paths produce different effective stroke contrast from the same font file. APCA cannot account for this.

### Ecosystem

- **Tool maturity.** Most mainstream design and dev tools (Figma's contrast checker, Adobe XD plugins, browser DevTools accessibility panels, axe-core, WAVE) still default to WCAG 2.x ratio. APCA is available in plugins and CLI tools but isn't yet "what the room is using." Adopting APCA internally has an onboarding cost — designers and engineers need to learn what `Lc 75` means versus the (deceptively) intuitive `4.5:1`.
- **Replacement for user testing? No.** APCA quantifies *predicted readability under typical viewing conditions*. It is a model, not a measurement. Real user testing — especially with members of disability communities — remains the highest-fidelity signal. APCA helps you avoid catching obvious failures in review; it does not replace iterative validation with real users.

## Further reading

- [APCA documentation hub](https://git.apcacontrast.com/) — the canonical reference site.
- [Myndex/SAPC-APCA](https://github.com/Myndex/SAPC-APCA) — algorithm derivation and historical context.
- [Myndex/apca-w3](https://github.com/Myndex/apca-w3) — the npm-published reference implementation this skill ports.
