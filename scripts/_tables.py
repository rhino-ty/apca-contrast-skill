"""Constants and lookup tables for APCA-W3 v0.1.9.

Sources:
  - fontMatrixAscend / fontDeltaAscend: apca-w3 0.1.9 (Myndex/apca-w3)
  - CSS named colors: CSS Color Module Level 4 (148 colors incl. rebeccapurple)
  - Display-P3, Rec.2020 → XYZ → sRGB matrices: CSS Color Module Level 4

Tables are kept verbatim from upstream so behavior matches the canonical library.
"""

# ============================================================
# fontLookupAPCA — apca-w3 0.1.9 (verbatim, Ascend variant)
# ============================================================
# Cell semantics (per Myndex):
#   999 — absolute non-text (font cannot be used at any size for any role)
#   777 — non-conformance (does not meet minimum APCA at this Lc/weight)
#     0 — not applicable / unused
#  >0  — minimum body-text font size in px for that (Lc, weight) cell
#
# To check pass/fail at a specific size:
#   round abs(Lc) to nearest 5, look up [Lc, weight] cell, then
#   pass if cell is a number > 0 AND requested size >= cell value.

CONTRAST_LEVELS = [
    0, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    55, 60, 65, 70, 75, 80, 85, 90, 95, 100,
    105, 110, 115, 120, 125,
]

WEIGHTS = [100, 200, 300, 400, 500, 600, 700, 800, 900]

# Rows aligned with CONTRAST_LEVELS, columns with WEIGHTS
FONT_MATRIX_ASCEND = [
    [999, 999, 999, 999, 999, 999, 999, 999, 999],   # Lc 0
    [999, 999, 999, 999, 999, 999, 999, 999, 999],   # Lc 10
    [777, 777, 777, 777, 777, 777, 777, 777, 777],   # Lc 15
    [777, 777, 777, 777, 777, 777, 777, 777, 777],   # Lc 20
    [777, 777, 777, 120, 120, 108,  96,  96,  96],   # Lc 25
    [777, 777, 120, 108, 108,  96,  72,  72,  72],   # Lc 30
    [777, 120, 108,  96,  72,  60,  48,  48,  48],   # Lc 35
    [120, 108,  96,  60,  48,  42,  32,  32,  32],   # Lc 40
    [108,  96,  72,  42,  32,  28,  24,  24,  24],   # Lc 45
    [ 96,  72,  60,  32,  28,  24,  21,  21,  21],   # Lc 50
    [ 80,  60,  48,  28,  24,  21,  18,  18,  18],   # Lc 55
    [ 72,  48,  42,  24,  21,  18,  16,  16,  18],   # Lc 60
    [ 68,  46,  32,  21.75, 19, 17,  15,  16,  18],  # Lc 65
    [ 64,  44,  28,  19.5,  18, 16,  14.5, 16, 18],  # Lc 70
    [ 60,  42,  24,  18,    16, 15,  14,   16, 18],  # Lc 75
    [ 56,  38.25, 23, 17.25, 15.81, 14.81, 14, 16, 18],  # Lc 80
    [ 52,  34.5,  22, 16.5,  15.625, 14.625, 14, 16, 18],  # Lc 85
    [ 48,  32,    21, 16,    15.5,   14.5,   14, 16, 18],  # Lc 90
    [ 45,  28,    19.5, 15.5, 15,    14,     13.5, 16, 18],  # Lc 95
    [ 42,  26.5,  18.5, 15,   14.5,  13.5,   13,   16, 18],  # Lc 100
    [ 39,  25,    18,   14.5, 14,    13,     12,   16, 18],  # Lc 105
    [ 36,  24,    18,   14,   13,    12,     11,   16, 18],  # Lc 110
    [ 34.5, 22.5, 17.25, 12.5, 11.875, 11.25, 10.625, 14.5, 16.5],  # Lc 115
    [ 33,   21,   16.5, 11,    10.75, 10.5,  10.25, 13,   15],   # Lc 120
    [ 32,   20,   16,   10,    10,    10,    10,    12,   14],   # Lc 125
]


# ============================================================
# CSS Named Colors (CSS Color Module Level 4)
# ============================================================
# 148 entries — 147 X11 names + rebeccapurple.
# Each entry maps to (r, g, b) in 0–255 sRGB.

NAMED_COLORS = {
    "aliceblue":            (240, 248, 255),
    "antiquewhite":         (250, 235, 215),
    "aqua":                 (  0, 255, 255),
    "aquamarine":           (127, 255, 212),
    "azure":                (240, 255, 255),
    "beige":                (245, 245, 220),
    "bisque":               (255, 228, 196),
    "black":                (  0,   0,   0),
    "blanchedalmond":       (255, 235, 205),
    "blue":                 (  0,   0, 255),
    "blueviolet":           (138,  43, 226),
    "brown":                (165,  42,  42),
    "burlywood":            (222, 184, 135),
    "cadetblue":            ( 95, 158, 160),
    "chartreuse":           (127, 255,   0),
    "chocolate":            (210, 105,  30),
    "coral":                (255, 127,  80),
    "cornflowerblue":       (100, 149, 237),
    "cornsilk":             (255, 248, 220),
    "crimson":              (220,  20,  60),
    "cyan":                 (  0, 255, 255),
    "darkblue":             (  0,   0, 139),
    "darkcyan":             (  0, 139, 139),
    "darkgoldenrod":        (184, 134,  11),
    "darkgray":             (169, 169, 169),
    "darkgreen":            (  0, 100,   0),
    "darkgrey":             (169, 169, 169),
    "darkkhaki":            (189, 183, 107),
    "darkmagenta":          (139,   0, 139),
    "darkolivegreen":       ( 85, 107,  47),
    "darkorange":           (255, 140,   0),
    "darkorchid":           (153,  50, 204),
    "darkred":              (139,   0,   0),
    "darksalmon":           (233, 150, 122),
    "darkseagreen":         (143, 188, 143),
    "darkslateblue":        ( 72,  61, 139),
    "darkslategray":        ( 47,  79,  79),
    "darkslategrey":        ( 47,  79,  79),
    "darkturquoise":        (  0, 206, 209),
    "darkviolet":           (148,   0, 211),
    "deeppink":             (255,  20, 147),
    "deepskyblue":          (  0, 191, 255),
    "dimgray":              (105, 105, 105),
    "dimgrey":              (105, 105, 105),
    "dodgerblue":           ( 30, 144, 255),
    "firebrick":            (178,  34,  34),
    "floralwhite":          (255, 250, 240),
    "forestgreen":          ( 34, 139,  34),
    "fuchsia":              (255,   0, 255),
    "gainsboro":            (220, 220, 220),
    "ghostwhite":           (248, 248, 255),
    "gold":                 (255, 215,   0),
    "goldenrod":            (218, 165,  32),
    "gray":                 (128, 128, 128),
    "green":                (  0, 128,   0),
    "greenyellow":          (173, 255,  47),
    "grey":                 (128, 128, 128),
    "honeydew":             (240, 255, 240),
    "hotpink":              (255, 105, 180),
    "indianred":            (205,  92,  92),
    "indigo":               ( 75,   0, 130),
    "ivory":                (255, 255, 240),
    "khaki":                (240, 230, 140),
    "lavender":             (230, 230, 250),
    "lavenderblush":        (255, 240, 245),
    "lawngreen":            (124, 252,   0),
    "lemonchiffon":         (255, 250, 205),
    "lightblue":            (173, 216, 230),
    "lightcoral":           (240, 128, 128),
    "lightcyan":            (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray":            (211, 211, 211),
    "lightgreen":           (144, 238, 144),
    "lightgrey":            (211, 211, 211),
    "lightpink":            (255, 182, 193),
    "lightsalmon":          (255, 160, 122),
    "lightseagreen":        ( 32, 178, 170),
    "lightskyblue":         (135, 206, 250),
    "lightslategray":       (119, 136, 153),
    "lightslategrey":       (119, 136, 153),
    "lightsteelblue":       (176, 196, 222),
    "lightyellow":          (255, 255, 224),
    "lime":                 (  0, 255,   0),
    "limegreen":            ( 50, 205,  50),
    "linen":                (250, 240, 230),
    "magenta":              (255,   0, 255),
    "maroon":               (128,   0,   0),
    "mediumaquamarine":     (102, 205, 170),
    "mediumblue":           (  0,   0, 205),
    "mediumorchid":         (186,  85, 211),
    "mediumpurple":         (147, 112, 219),
    "mediumseagreen":       ( 60, 179, 113),
    "mediumslateblue":      (123, 104, 238),
    "mediumspringgreen":    (  0, 250, 154),
    "mediumturquoise":      ( 72, 209, 204),
    "mediumvioletred":      (199,  21, 133),
    "midnightblue":         ( 25,  25, 112),
    "mintcream":            (245, 255, 250),
    "mistyrose":            (255, 228, 225),
    "moccasin":             (255, 228, 181),
    "navajowhite":          (255, 222, 173),
    "navy":                 (  0,   0, 128),
    "oldlace":              (253, 245, 230),
    "olive":                (128, 128,   0),
    "olivedrab":            (107, 142,  35),
    "orange":               (255, 165,   0),
    "orangered":            (255,  69,   0),
    "orchid":               (218, 112, 214),
    "palegoldenrod":        (238, 232, 170),
    "palegreen":            (152, 251, 152),
    "paleturquoise":        (175, 238, 238),
    "palevioletred":        (219, 112, 147),
    "papayawhip":           (255, 239, 213),
    "peachpuff":            (255, 218, 185),
    "peru":                 (205, 133,  63),
    "pink":                 (255, 192, 203),
    "plum":                 (221, 160, 221),
    "powderblue":           (176, 224, 230),
    "purple":               (128,   0, 128),
    "rebeccapurple":        (102,  51, 153),
    "red":                  (255,   0,   0),
    "rosybrown":            (188, 143, 143),
    "royalblue":            ( 65, 105, 225),
    "saddlebrown":          (139,  69,  19),
    "salmon":               (250, 128, 114),
    "sandybrown":           (244, 164,  96),
    "seagreen":             ( 46, 139,  87),
    "seashell":             (255, 245, 238),
    "sienna":               (160,  82,  45),
    "silver":               (192, 192, 192),
    "skyblue":              (135, 206, 235),
    "slateblue":            (106,  90, 205),
    "slategray":            (112, 128, 144),
    "slategrey":            (112, 128, 144),
    "snow":                 (255, 250, 250),
    "springgreen":          (  0, 255, 127),
    "steelblue":            ( 70, 130, 180),
    "tan":                  (210, 180, 140),
    "teal":                 (  0, 128, 128),
    "thistle":              (216, 191, 216),
    "tomato":               (255,  99,  71),
    "turquoise":            ( 64, 224, 208),
    "violet":               (238, 130, 238),
    "wheat":                (245, 222, 179),
    "white":                (255, 255, 255),
    "whitesmoke":           (245, 245, 245),
    "yellow":               (255, 255,   0),
    "yellowgreen":          (154, 205,  50),
}

# Special: transparent (alpha=0). Resolved separately.
TRANSPARENT = (0, 0, 0, 0.0)


# ============================================================
# Wide-gamut → sRGB matrices (CSS Color Module Level 4, D65)
# ============================================================
# All operate on linear-light values (gamma-decoded inputs).
# Inputs and outputs are linear; gamma encoding/decoding handled by caller.

# Display-P3 (linear) → linear sRGB
# Derived from: Display-P3 → XYZ_D65 → sRGB matrices
P3_TO_SRGB_LINEAR = (
    ( 1.2249401762010375, -0.22494017620103751,  0.0),
    (-0.04205696857469864, 1.0420569685746986,   0.0),
    (-0.019637554590334566, -0.07863604242080865, 1.0982735970111433),
)

# Rec.2020 (linear) → linear sRGB
REC2020_TO_SRGB_LINEAR = (
    ( 1.6604910021084345,  -0.5876411310979599,  -0.07284987101047455),
    (-0.12455047452159074,  1.1328999742809481,  -0.008349499759357446),
    (-0.018150763354905326, -0.10057889800800737, 1.1187296613629127),
)
