#!/usr/bin/env python3
"""APCA-W3 v0.1.9 contrast calculator with WCAG-equivalent verdicts.

Implements the Accessible Perceptual Contrast Algorithm (APCA-W3 0.1.9)
including the official fontLookupAPCA table for precise pass/fail per
font size and weight. No external dependencies (Python stdlib only).

Reference:
  - https://github.com/Myndex/apca-w3
  - Algorithm constants frozen at 0.0.98G-4g (Feb 2021)

Color formats supported:
  - Hex:           #fff, #ffffff, #fffffff0
  - rgb()/rgba():  rgb(255,255,255), rgb(255 255 255 / 50%)
  - hsl()/hsla():  hsl(0 0% 50%), hsla(120, 100%, 25%, 0.5)
  - oklch()/oklab: oklch(0.205 0 0), oklab(0.5 0.05 -0.1)
  - color():       color(srgb 1 0 0), color(display-p3 1 0 0),
                   color(rec2020 1 0 0), color(srgb-linear 0.5 0.5 0.5)
  - Named:         red, white, rebeccapurple, transparent, ...

Usage:
  apca.py <fg> <bg>                          Single pair
  apca.py --json <fg> <bg>                   Single pair, JSON
  apca.py --batch pairs.json                 Batch from JSON
  apca.py --from-tailwind globals.css        Extract tokens from Tailwind v4 CSS
  apca.py --reverse <bg> <target_lc> <weight> <size>
                                              Find a color that hits target Lc
"""

import argparse
import json
import math
import re
import sys
from typing import Optional, Tuple, List, Dict, Any

from _tables import (
    CONTRAST_LEVELS,
    WEIGHTS,
    FONT_MATRIX_ASCEND,
    NAMED_COLORS,
    P3_TO_SRGB_LINEAR,
    REC2020_TO_SRGB_LINEAR,
)


# ============================================================
# APCA-W3 v0.1.9 constants (frozen at 0.0.98G-4g)
# ============================================================
MAIN_TRC = 2.4
S_RCO, S_GCO, S_BCO = 0.2126729, 0.7151522, 0.0721750
NORM_BG, NORM_TXT = 0.56, 0.57
REV_TXT, REV_BG = 0.62, 0.65
BLK_THRS, BLK_CLMP = 0.022, 1.414
SCALE_BOW, LO_BOW_OFFSET = 1.14, 0.027
SCALE_WOB, LO_WOB_OFFSET = 1.14, 0.027
DELTA_Y_MIN = 0.0005
LO_CLIP = 0.1


# ============================================================
# Color parsing
# ============================================================
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3,8})$")
RGB_RE = re.compile(
    r"^rgba?\(\s*([\d.]+%?)[,\s]+([\d.]+%?)[,\s]+([\d.]+%?)"
    r"(?:\s*[,/]\s*([\d.]+%?))?\s*\)$",
    re.IGNORECASE,
)
HSL_RE = re.compile(
    r"^hsla?\(\s*([\d.]+)(?:deg|rad|turn)?\s*[,\s]\s*([\d.]+)%\s*[,\s]\s*([\d.]+)%"
    r"(?:\s*[,/]\s*([\d.]+%?))?\s*\)$",
    re.IGNORECASE,
)
OKLCH_RE = re.compile(
    r"^oklch\(\s*([\d.]+%?)\s+([\d.]+%?)\s+(-?[\d.]+)(?:deg)?"
    r"(?:\s*/\s*([\d.]+%?))?\s*\)$",
    re.IGNORECASE,
)
OKLAB_RE = re.compile(
    r"^oklab\(\s*([\d.]+%?)\s+(-?[\d.]+%?)\s+(-?[\d.]+%?)"
    r"(?:\s*/\s*([\d.]+%?))?\s*\)$",
    re.IGNORECASE,
)
COLOR_FN_RE = re.compile(
    r"^color\(\s*([a-z0-9-]+)\s+(-?[\d.]+%?)\s+(-?[\d.]+%?)\s+(-?[\d.]+%?)"
    r"(?:\s*/\s*([\d.]+%?))?\s*\)$",
    re.IGNORECASE,
)


def _pct(v: str, base: float = 1.0) -> float:
    v = v.strip()
    if v.endswith("%"):
        return float(v[:-1]) / 100.0 * base
    return float(v)


def _rgb_component(v: str) -> int:
    """Accept '255', '100%', '0.5' (fraction)."""
    v = v.strip()
    if v.endswith("%"):
        return _clamp_byte(round(float(v[:-1]) / 100.0 * 255))
    f = float(v)
    if f <= 1.0 and "." in v:
        # Fractional shorthand sometimes seen — treat as 0–1 mapped to 0–255
        return _clamp_byte(round(f * 255))
    return _clamp_byte(round(f))


def _clamp_byte(v: int) -> int:
    return max(0, min(255, int(v)))


def parse_color(s: str) -> Tuple[Tuple[int, int, int], float]:
    """Parse any supported color string → ((r, g, b), alpha) in 0–255 sRGB."""
    s = s.strip()
    s_lower = s.lower()

    # Named color
    if s_lower == "transparent":
        return (0, 0, 0), 0.0
    if s_lower in NAMED_COLORS:
        return NAMED_COLORS[s_lower], 1.0

    # Hex
    m = HEX_RE.match(s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            return tuple(int(c * 2, 16) for c in h), 1.0  # type: ignore
        if len(h) == 4:
            r, g, b, a = (int(c * 2, 16) for c in h)
            return (r, g, b), a / 255.0
        if len(h) == 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)), 1.0
        if len(h) == 8:
            return (
                (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)),
                int(h[6:8], 16) / 255.0,
            )
        raise ValueError(f"Invalid hex: {s}")

    # rgb() / rgba()
    m = RGB_RE.match(s)
    if m:
        r, g, b = (_rgb_component(m.group(i)) for i in (1, 2, 3))
        a = _pct(m.group(4), 1.0) if m.group(4) else 1.0
        return (r, g, b), a

    # hsl() / hsla()
    m = HSL_RE.match(s)
    if m:
        h_raw = s_lower
        h_deg = _hue_to_deg(h_raw, float(m.group(1)))
        sat = float(m.group(2)) / 100.0
        lit = float(m.group(3)) / 100.0
        a = _pct(m.group(4), 1.0) if m.group(4) else 1.0
        return _hsl_to_srgb(h_deg, sat, lit), a

    # oklch()
    m = OKLCH_RE.match(s)
    if m:
        L = _pct(m.group(1), 1.0)
        C = _pct(m.group(2), 0.4)  # 100% chroma scale per CSS spec
        h = float(m.group(3))
        a = _pct(m.group(4), 1.0) if m.group(4) else 1.0
        return _oklch_to_srgb(L, C, h), a

    # oklab()
    m = OKLAB_RE.match(s)
    if m:
        L = _pct(m.group(1), 1.0)
        a_ = _pct(m.group(2), 0.4)
        b_ = _pct(m.group(3), 0.4)
        alpha = _pct(m.group(4), 1.0) if m.group(4) else 1.0
        return _oklab_to_srgb(L, a_, b_), alpha

    # color() function
    m = COLOR_FN_RE.match(s)
    if m:
        space = m.group(1).lower()
        c1 = _pct(m.group(2), 1.0)
        c2 = _pct(m.group(3), 1.0)
        c3 = _pct(m.group(4), 1.0)
        alpha = _pct(m.group(5), 1.0) if m.group(5) else 1.0
        return _color_fn_to_srgb(space, c1, c2, c3), alpha

    raise ValueError(f"Unsupported color: {s!r}")


def _hue_to_deg(raw: str, value: float) -> float:
    if "rad" in raw:
        return math.degrees(value)
    if "turn" in raw:
        return value * 360.0
    return value  # deg or unitless


# ----- HSL → sRGB -----
def _hsl_to_srgb(h_deg: float, s: float, l: float) -> Tuple[int, int, int]:
    h = (h_deg % 360.0) / 360.0
    if s == 0:
        v = round(l * 255)
        return (v, v, v)
    q = l + s - l * s if l >= 0.5 else l * (1 + s)
    p = 2 * l - q

    def to_rgb(t: float) -> int:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            v = p + (q - p) * 6 * t
        elif t < 1 / 2:
            v = q
        elif t < 2 / 3:
            v = p + (q - p) * (2 / 3 - t) * 6
        else:
            v = p
        return _clamp_byte(round(v * 255))

    return (to_rgb(h + 1 / 3), to_rgb(h), to_rgb(h - 1 / 3))


# ----- Oklch / Oklab → sRGB -----
def _oklch_to_srgb(L: float, C: float, h_deg: float) -> Tuple[int, int, int]:
    h_rad = math.radians(h_deg)
    return _oklab_to_srgb(L, C * math.cos(h_rad), C * math.sin(h_rad))


def _oklab_to_srgb(L: float, a: float, b: float) -> Tuple[int, int, int]:
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r_lin = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g_lin = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_lin = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return tuple(_lin_to_srgb_byte(c) for c in (r_lin, g_lin, b_lin))  # type: ignore


# ----- color() function dispatch -----
def _color_fn_to_srgb(
    space: str, c1: float, c2: float, c3: float
) -> Tuple[int, int, int]:
    if space == "srgb":
        return tuple(_clamp_byte(round(c * 255)) for c in (c1, c2, c3))  # type: ignore
    if space == "srgb-linear":
        return tuple(_lin_to_srgb_byte(c) for c in (c1, c2, c3))  # type: ignore
    if space in ("display-p3", "p3"):
        return _wide_gamut_to_srgb((c1, c2, c3), P3_TO_SRGB_LINEAR, gamma=2.4)
    if space in ("rec2020", "rec.2020", "bt2020"):
        return _wide_gamut_to_srgb((c1, c2, c3), REC2020_TO_SRGB_LINEAR, gamma=2.4)
    raise ValueError(f"Unsupported color() space: {space}")


def _wide_gamut_to_srgb(
    rgb: Tuple[float, float, float],
    matrix: Tuple[Tuple[float, float, float], ...],
    gamma: float = 2.4,
) -> Tuple[int, int, int]:
    # Gamma-decode wide-gamut input (uses sRGB-like transfer for Display-P3,
    # BT.2020 EOTF approximated by 2.4 — close enough for APCA's tolerance).
    lin = tuple(_srgb_to_linear(c) for c in rgb)
    out = tuple(
        matrix[i][0] * lin[0] + matrix[i][1] * lin[1] + matrix[i][2] * lin[2]
        for i in range(3)
    )
    return tuple(_lin_to_srgb_byte(c) for c in out)  # type: ignore


def _srgb_to_linear(c: float) -> float:
    c = max(0.0, min(1.0, c))
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lin_to_srgb_byte(c: float) -> int:
    c = max(0.0, min(1.0, c))
    srgb = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return _clamp_byte(round(srgb * 255))


# ============================================================
# Alpha compositing (UNOFFICIAL extension)
# ============================================================
# APCA spec officially does NOT support alpha. This pre-composites the
# foreground over the background in sRGB (not linear-light), which is the
# pragmatic approximation most tools use. Document this limitation.

def composite(
    fg: Tuple[int, int, int], fg_alpha: float, bg: Tuple[int, int, int]
) -> Tuple[int, int, int]:
    if fg_alpha >= 1.0:
        return fg
    if fg_alpha <= 0.0:
        return bg
    return tuple(  # type: ignore
        int(round(fg_alpha * fg[i] + (1 - fg_alpha) * bg[i])) for i in range(3)
    )


# ============================================================
# APCA core
# ============================================================
def srgb_to_y(rgb: Tuple[int, int, int]) -> float:
    r, g, b = (c / 255.0 for c in rgb)
    return S_RCO * (r ** MAIN_TRC) + S_GCO * (g ** MAIN_TRC) + S_BCO * (b ** MAIN_TRC)


def apca_lc(txt_rgb: Tuple[int, int, int], bg_rgb: Tuple[int, int, int]) -> float:
    """Return signed Lc. Positive = dark text on light bg, negative = inverse."""
    txt_y = srgb_to_y(txt_rgb)
    bg_y = srgb_to_y(bg_rgb)

    if txt_y < BLK_THRS:
        txt_y = txt_y + (BLK_THRS - txt_y) ** BLK_CLMP
    if bg_y < BLK_THRS:
        bg_y = bg_y + (BLK_THRS - bg_y) ** BLK_CLMP

    if abs(bg_y - txt_y) < DELTA_Y_MIN:
        return 0.0

    if bg_y > txt_y:  # Dark text on light bg
        sapc = (bg_y ** NORM_BG - txt_y ** NORM_TXT) * SCALE_BOW
        out = 0.0 if sapc < LO_CLIP else (sapc - LO_BOW_OFFSET)
    else:  # Light text on dark bg
        sapc = (bg_y ** REV_BG - txt_y ** REV_TXT) * SCALE_WOB
        out = 0.0 if sapc > -LO_CLIP else (sapc + LO_WOB_OFFSET)

    return round(out * 100, 1)


# ============================================================
# fontLookupAPCA — official table lookup
# ============================================================
def _round_lc_to_table(lc_abs: float) -> int:
    """Round abs(Lc) down to nearest 5 within table bounds."""
    lc = max(0.0, min(125.0, lc_abs))
    return int(lc // 5) * 5


def font_min_size(lc: float, weight: int) -> Optional[float]:
    """Return minimum body font-size (px) that passes for given Lc and weight.
    None means non-conformant at this weight (777/999 sentinel)."""
    if weight not in WEIGHTS:
        # Snap to nearest valid weight
        weight = min(WEIGHTS, key=lambda w: abs(w - weight))
    lc_key = _round_lc_to_table(abs(lc))
    if lc_key not in CONTRAST_LEVELS:
        return None
    row = FONT_MATRIX_ASCEND[CONTRAST_LEVELS.index(lc_key)]
    cell = row[WEIGHTS.index(weight)]
    if cell in (0, 777, 999):
        return None
    return float(cell)


def passes_at(lc: float, size_px: float, weight: int) -> bool:
    """Does this Lc / weight pass at requested font size?"""
    min_size = font_min_size(lc, weight)
    return min_size is not None and size_px >= min_size


# ============================================================
# Common-size matrix view
# ============================================================
TYPICAL_SIZES = [12, 14, 16, 18, 24, 32]
TYPICAL_WEIGHTS = [400, 500, 600, 700]


def size_weight_matrix(lc: float) -> List[Dict[str, Any]]:
    """For a given Lc, return pass/fail for typical (size, weight) cells."""
    rows = []
    for size in TYPICAL_SIZES:
        row: Dict[str, Any] = {"size_px": size}
        for w in TYPICAL_WEIGHTS:
            row[f"w{w}"] = "PASS" if passes_at(lc, size, w) else "fail"
        rows.append(row)
    return rows


# ============================================================
# Reverse APCA — find a foreground that hits target Lc on a given bg
# ============================================================
def reverse_apca(
    bg_rgb: Tuple[int, int, int], target_lc: float, polarity: str = "auto"
) -> Optional[Tuple[int, int, int]]:
    """Binary-search a neutral grey foreground that hits target |Lc| on bg.

    polarity:
      'auto' — choose darker or lighter based on bg luminance
      'BoW'  — force dark text (positive Lc)
      'WoB'  — force light text (negative Lc)

    Returns greyscale (r, r, r) or None if unreachable.
    """
    bg_y = srgb_to_y(bg_rgb)
    if polarity == "auto":
        polarity = "BoW" if bg_y > 0.4 else "WoB"

    target = abs(target_lc)
    lo, hi = (0, bg_rgb[0]) if polarity == "BoW" else (bg_rgb[0], 255)
    # Walk through the full grayscale range to be safe regardless of bg color
    if polarity == "BoW":
        lo, hi = 0, 255
    else:
        lo, hi = 0, 255

    # Use bisection on V in 0..255 grey
    best = None
    best_diff = float("inf")
    for _ in range(40):
        mid = (lo + hi) // 2
        fg = (mid, mid, mid)
        lc = abs(apca_lc(fg, bg_rgb))
        if abs(lc - target) < best_diff:
            best_diff = abs(lc - target)
            best = fg
        if lc < target:
            # Need more contrast → push grey further from bg
            if polarity == "BoW":
                hi = mid - 1  # darker
            else:
                lo = mid + 1  # lighter
        else:
            if polarity == "BoW":
                lo = mid + 1
            else:
                hi = mid - 1
        if lo > hi:
            break
    return best


# ============================================================
# Verdict (Bronze-style summary, derived from fontLookupAPCA)
# ============================================================
def verdict_for(lc: float) -> str:
    """Human-readable verdict using fontLookupAPCA at weight=400."""
    abs_lc = abs(lc)
    min_size = font_min_size(lc, 400)
    if min_size is None:
        if abs_lc < 15:
            return "Fail — insufficient contrast"
        if abs_lc < 30:
            return "Fail for text — decorative / disabled UI only"
        return "Fail for body text — non-text UI / large headlines only"
    if min_size <= 12:
        return f"Pass — body text any size (≥{min_size:g}px @ 400wt)"
    if min_size <= 14:
        return f"Pass — body text ≥{min_size:g}px @ 400wt"
    if min_size <= 16:
        return f"Pass — body minimum ≥{min_size:g}px @ 400wt"
    if min_size <= 18:
        return f"Pass — large text only ≥{min_size:g}px @ 400wt"
    return f"Pass — headlines only ≥{min_size:g}px @ 400wt"


# ============================================================
# Single-pair evaluation
# ============================================================
def evaluate(fg_str: str, bg_str: str, *, matrix: bool = False) -> Dict[str, Any]:
    fg_rgb, fg_alpha = parse_color(fg_str)
    bg_rgb, bg_alpha = parse_color(bg_str)

    bg_composited = bg_alpha < 1.0
    if bg_composited:
        bg_rgb = composite(bg_rgb, bg_alpha, (255, 255, 255))

    fg_composited = fg_alpha < 1.0
    composed_fg = composite(fg_rgb, fg_alpha, bg_rgb) if fg_composited else fg_rgb

    lc = apca_lc(composed_fg, bg_rgb)

    result = {
        "fg_input": fg_str,
        "bg_input": bg_str,
        "fg_alpha": fg_alpha,
        "bg_rgb": list(bg_rgb),
        "composed_fg_rgb": list(composed_fg),
        "lc": lc,
        "polarity": "BoW" if lc > 0 else "WoB" if lc < 0 else "none",
        "verdict": verdict_for(lc),
        "min_size_per_weight": {
            f"w{w}": font_min_size(lc, w) for w in TYPICAL_WEIGHTS
        },
        "alpha_compositing_used": fg_composited or bg_composited,
    }
    if matrix:
        result["size_weight_matrix"] = size_weight_matrix(lc)
    return result


# ============================================================
# Batch mode
# ============================================================
def load_batch(path: str) -> List[Dict[str, str]]:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "background" in data and "tokens" in data:
        bg = data["background"]
        return [{"name": k, "fg": v, "bg": bg} for k, v in data["tokens"].items()]
    raise ValueError("Batch file must be a list or {background, tokens}")


def evaluate_batch(
    pairs: List[Dict[str, str]], *, matrix: bool = False
) -> List[Dict[str, Any]]:
    results = []
    for pair in pairs:
        try:
            r = evaluate(pair["fg"], pair["bg"], matrix=matrix)
            r["name"] = pair.get("name", "")
            results.append(r)
        except Exception as e:
            results.append(
                {
                    "name": pair.get("name", ""),
                    "fg_input": pair.get("fg"),
                    "bg_input": pair.get("bg"),
                    "error": str(e),
                }
            )
    return results


# ============================================================
# Tailwind v4 globals.css extractor
# ============================================================
TAILWIND_BLOCK_RE = re.compile(
    r"(:root|\.dark)\s*\{([^}]+)\}", re.DOTALL
)
TAILWIND_VAR_RE = re.compile(
    r"--([a-z0-9-]+)\s*:\s*([^;]+);", re.IGNORECASE
)


def extract_tailwind_tokens(css_path: str) -> Dict[str, Dict[str, str]]:
    """Parse Tailwind v4 globals.css and return {mode: {token: value}}.

    Recognizes :root (light) and .dark blocks.
    """
    with open(css_path) as f:
        css = f.read()
    modes: Dict[str, Dict[str, str]] = {"light": {}, "dark": {}}
    for selector, body in TAILWIND_BLOCK_RE.findall(css):
        mode = "dark" if selector == ".dark" else "light"
        for var, value in TAILWIND_VAR_RE.findall(body):
            value = value.strip()
            if any(value.startswith(p) for p in ("oklch", "oklab", "rgb", "hsl", "#")):
                modes[mode][var] = value
            elif value.lower() in NAMED_COLORS or value.lower() == "transparent":
                modes[mode][var] = value
    return modes


def audit_tailwind(
    css_path: str,
    bg_token: str = "background",
    fg_tokens: Optional[List[str]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Audit a Tailwind theme: pair each fg token against bg in both modes."""
    modes = extract_tailwind_tokens(css_path)
    fg_tokens = fg_tokens or [
        "foreground",
        "muted-foreground",
        "primary",
        "secondary-foreground",
        "accent-foreground",
        "destructive",
        "card-foreground",
        "popover-foreground",
        "border",
    ]
    audit: Dict[str, List[Dict[str, Any]]] = {}
    for mode, tokens in modes.items():
        if bg_token not in tokens:
            audit[mode] = [{"error": f"--{bg_token} not found in {mode}"}]
            continue
        bg = tokens[bg_token]
        rows = []
        for fg_name in fg_tokens:
            if fg_name not in tokens:
                continue
            try:
                r = evaluate(tokens[fg_name], bg)
                r["name"] = f"{fg_name} on {bg_token}"
                rows.append(r)
            except Exception as e:
                rows.append({"name": fg_name, "error": str(e)})
        audit[mode] = rows
    return audit


# ============================================================
# Output formatting
# ============================================================
def format_single(r: Dict[str, Any]) -> str:
    fg_hex = "#{:02x}{:02x}{:02x}".format(*r["composed_fg_rgb"])
    bg_hex = "#{:02x}{:02x}{:02x}".format(*r["bg_rgb"])
    lines = [
        f"Text:       {r['fg_input']}  →  {fg_hex} (alpha={r['fg_alpha']:.2f})",
        f"Background: {r['bg_input']}  →  {bg_hex}",
        f"Lc:         {r['lc']:+.1f}  ({r['polarity']})",
        f"Verdict:    {r['verdict']}",
        "",
        "Min font size (px) per weight:",
    ]
    for w in TYPICAL_WEIGHTS:
        v = r["min_size_per_weight"].get(f"w{w}")
        cell = f"{v:g}" if isinstance(v, (int, float)) else "—"
        lines.append(f"  {w}wt: {cell}")
    if r.get("alpha_compositing_used"):
        lines.append("")
        lines.append("⚠ Alpha compositing applied (unofficial — APCA spec omits alpha)")
    if "size_weight_matrix" in r:
        lines.append("")
        lines.append(_format_matrix(r["size_weight_matrix"]))
    return "\n".join(lines)


def _format_matrix(rows: List[Dict[str, Any]]) -> str:
    header = f"{'size':>6} | " + " | ".join(f"{w}wt" for w in TYPICAL_WEIGHTS)
    sep = "-" * len(header)
    out = [header, sep]
    for row in rows:
        cells = [f"{row[f'w{w}']:^4}" for w in TYPICAL_WEIGHTS]
        out.append(f"{row['size_px']:>5}px | " + " | ".join(cells))
    return "\n".join(out)


def format_batch_table(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "(no pairs)"
    name_w = max(len(r.get("name") or "") for r in results)
    name_w = max(name_w, 4)
    header = f"| {'Name'.ljust(name_w)} | {'Lc':>6} | Verdict"
    sep = f"|{'-' * (name_w + 2)}|{'-' * 8}|" + "-" * 50
    rows = [header, sep]
    for r in results:
        name = (r.get("name") or "").ljust(name_w)
        if "error" in r:
            rows.append(f"| {name} | {'ERR':>6} | {r['error']}")
            continue
        rows.append(f"| {name} | {r['lc']:+6.1f} | {r['verdict']}")
    return "\n".join(rows)


def format_tailwind_audit(audit: Dict[str, List[Dict[str, Any]]]) -> str:
    out = []
    for mode in ("light", "dark"):
        if mode not in audit:
            continue
        out.append(f"## {mode.upper()} mode")
        out.append(format_batch_table(audit[mode]))
        out.append("")
    return "\n".join(out)


# ============================================================
# CLI
# ============================================================
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="APCA-W3 v0.1.9 contrast calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("fg", nargs="?", help="Foreground (text) color")
    p.add_argument("bg", nargs="?", help="Background color")
    p.add_argument("--batch", help="Path to JSON batch file")
    p.add_argument(
        "--from-tailwind",
        help="Path to Tailwind v4 globals.css — extract :root + .dark blocks",
    )
    p.add_argument(
        "--bg-token",
        default="background",
        help="Background token name when using --from-tailwind (default: background)",
    )
    p.add_argument(
        "--reverse",
        nargs=2,
        metavar=("BG", "TARGET_LC"),
        help="Find a grey foreground that hits target |Lc| on given bg",
    )
    p.add_argument("--matrix", action="store_true", help="Show size×weight matrix")
    p.add_argument("--json", action="store_true", help="JSON output")
    args = p.parse_args(argv)

    if args.reverse:
        bg_str, target = args.reverse
        bg_rgb, _ = parse_color(bg_str)
        fg = reverse_apca(bg_rgb, float(target))
        if fg is None:
            print("No solution found", file=sys.stderr)
            return 1
        lc = apca_lc(fg, bg_rgb)
        fg_hex = "#{:02x}{:02x}{:02x}".format(*fg)
        result = {
            "background": bg_str,
            "target_lc": float(target),
            "found_fg_hex": fg_hex,
            "actual_lc": lc,
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(
                f"For bg {bg_str}, target |Lc|={target}: "
                f"use {fg_hex} (actual Lc {lc:+.1f})"
            )
        return 0

    if args.from_tailwind:
        audit = audit_tailwind(args.from_tailwind, bg_token=args.bg_token)
        if args.json:
            print(json.dumps(audit, indent=2))
        else:
            print(format_tailwind_audit(audit))
        return 0

    if args.batch:
        pairs = load_batch(args.batch)
        results = evaluate_batch(pairs, matrix=args.matrix)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(format_batch_table(results))
        return 0

    if not args.fg or not args.bg:
        p.error("Provide <fg> <bg>, --batch, --from-tailwind, or --reverse")

    result = evaluate(args.fg, args.bg, matrix=args.matrix)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_single(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
