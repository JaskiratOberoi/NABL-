"""Builds organo-logo.png: pinwheel brush ring + "rgano" / "Biotech" wordmark.

Geometry is in reference-photo pixels (774 x 304 crop of the supplied letterhead)
and rendered at SS x supersampling, then downsampled to OUT_SCALE.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "organo-logo.png"
ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"

OUT_SCALE = 4
SS = 3
K = OUT_SCALE * SS

CROP = (50, 66, 730, 282)
TEXT = (76, 76, 76, 255)

RING_C = (131.0, 148.0)
RING_R = 73.0
RING_T = 12.0
OVERLAP = 13.0

LETTERS = [("r", 226), ("g", 288), ("a", 402), ("n", 518), ("o", 626)]
BASELINE = 212.0
X_HEIGHT = 104.0
BIOTECH_RIGHT = 722.0
BIOTECH_BASELINE = 273.0
BIOTECH_INK_W = 259.0

# clockwise strokes: (start angle, end angle, start colour, end colour)
STROKES = [
    (185.0, 95.0, (160, 82, 66), (120, 50, 44)),
    (95.0, 5.0, (112, 48, 48), (122, 50, 60)),
    (5.0, -85.0, (126, 52, 68), (150, 92, 108)),
    (-85.0, -175.0, (150, 104, 124), (190, 156, 168)),
]


def px(x: float, y: float) -> tuple[float, float]:
    return ((x - CROP[0]) * K, (y - CROP[1]) * K)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def draw_ring(d: ImageDraw.ImageDraw) -> None:
    cx, cy = RING_C
    for a0, a1, c0, c1 in STROKES:
        span = (a0 - a1) + OVERLAP
        steps = 240
        pts_out, pts_in, cols = [], [], []
        for i in range(steps + 1):
            u = i / steps
            ang = math.radians(a0 - u * span)
            w = RING_T * math.sin(math.pi * u) ** 0.85
            mid = RING_R - RING_T * 0.75 + RING_T * 0.62 * u
            ro, ri = mid + w / 2, mid - w / 2
            pts_out.append((cx + ro * math.cos(ang), cy - ro * math.sin(ang)))
            pts_in.append((cx + ri * math.cos(ang), cy - ri * math.sin(ang)))
            cols.append(lerp(c0, c1, u))
        for i in range(steps):
            quad = [pts_out[i], pts_out[i + 1], pts_in[i + 1], pts_in[i]]
            d.polygon([px(*p) for p in quad], fill=cols[i] + (255,))
            # seam cover between adjacent quads
            d.line([px(*pts_out[i + 1]), px(*pts_in[i + 1])], fill=cols[i] + (255,), width=2)


def font_for_xheight(xh_px: float) -> ImageFont.FreeTypeFont:
    probe = ImageFont.truetype(ARIAL, 1000)
    l, t, r, b = probe.getbbox("x", anchor="ls")
    size = xh_px * K * 1000 / (b - t)
    return ImageFont.truetype(ARIAL, round(size))


def draw_text(d: ImageDraw.ImageDraw) -> None:
    font = font_for_xheight(X_HEIGHT)
    by = (BASELINE - CROP[1]) * K
    for ch, ink_left in LETTERS:
        l, _, _, _ = font.getbbox(ch, anchor="ls")
        d.text(((ink_left - CROP[0]) * K - l, by), ch, font=font, fill=TEXT, anchor="ls")

    probe = ImageFont.truetype(ARIAL, 1000)
    l, _, r, _ = probe.getbbox("Biotech", anchor="ls")
    size = round(BIOTECH_INK_W * K * 1000 / (r - l))
    bfont = ImageFont.truetype(ARIAL, size)
    l, _, r, _ = bfont.getbbox("Biotech", anchor="ls")
    x = (BIOTECH_RIGHT - CROP[0]) * K - r
    d.text((x, (BIOTECH_BASELINE - CROP[1]) * K), "Biotech", font=bfont, fill=TEXT, anchor="ls")


def main() -> None:
    w = (CROP[2] - CROP[0]) * K
    h = (CROP[3] - CROP[1]) * K
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    draw_ring(d)
    draw_text(d)
    img = img.resize((w // SS, h // SS), Image.Resampling.LANCZOS)
    img.save(OUT)
    print(f"{OUT.name}: {img.size[0]}x{img.size[1]}")


if __name__ == "__main__":
    main()
