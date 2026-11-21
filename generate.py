#!/usr/bin/env python3
"""Render the VELMORA travel poster (build-time renderer).

Draws a vintage travel poster for Velmora, a place that does not exist:
one crescent islet, one coral lighthouse, a ringed planet hanging over a
dusk sea, and the invented name set large in the lower band. Pure Pillow,
deterministic (seeded), 1024x1024, writes assets/entry.png.

Run:  python3 generate.py
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "entry.png"

W, H = 1024, 1024
RNG = random.Random(7)

TITLE_FONT = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
TITLE_FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

# ---- palette -------------------------------------------------------------
INK = (20, 25, 48)          # deep indigo, bottom band
CREAM = (247, 234, 209)     # poster cream
GOLD = (217, 168, 90)       # keyline gold
SKY_TOP = (30, 38, 78)
SKY_MID = (88, 56, 106)
SKY_LOW = (198, 102, 82)
SKY_HORIZON = (242, 166, 94)
SEA_TOP = (214, 141, 96)
SEA_MID = (20, 96, 107)
SEA_LOW = (13, 58, 77)
ROCK = (36, 26, 56)
TOWER = (243, 226, 200)
LANTERN_GLOW = (255, 214, 138)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def vgrad(img, y0, y1, stops):
    """Vertical gradient over [y0, y1); stops = [(pos0..1, color), ...]."""
    d = ImageDraw.Draw(img)
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                tt = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                d.line([(0, y), (W - 1, y)], fill=lerp_color(c0, c1, tt))
                break


def radial_glow(layer, cx, cy, radius, color, peak=150):
    """Soft radial glow painted onto an RGBA overlay layer."""
    d = ImageDraw.Draw(layer)
    steps = 24
    for i in range(steps, 0, -1):
        r = radius * i / steps
        alpha = int(peak * (1 - i / steps) ** 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=color + (alpha,))


def tracked_width(font, text, tracking):
    total = 0
    for ch in text:
        total += font.getlength(ch) + tracking
    return total - tracking


def draw_tracked(d, cx, y, text, font, tracking, fill, shadow=None):
    """Draw text centred on cx with letter tracking; y is the top."""
    w = tracked_width(font, text, tracking)
    x = cx - w / 2
    asc, desc = font.getmetrics()
    for ch in text:
        if shadow is not None:
            d.text((x + 4, y + 5), ch, font=font, fill=shadow)
        d.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return w


def main():
    img = Image.new("RGB", (W, H), SKY_TOP)
    d = ImageDraw.Draw(img)

    # ---- sky -----------------------------------------------------------
    vgrad(img, 0, 610, [(0.0, SKY_TOP), (0.45, SKY_MID),
                        (0.8, SKY_LOW), (1.0, SKY_HORIZON)])

    # stars, only in the upper sky, kept clear of the planet
    for _ in range(110):
        x = RNG.uniform(30, 994)
        y = RNG.uniform(30, 330)
        if math.hypot(x - 720, y - 205) < 190:
            continue
        r = RNG.uniform(0.6, 1.8)
        a = RNG.uniform(0.35, 0.95)
        col = lerp_color((255, 255, 255), SKY_TOP, 1 - a)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    # soft warm clouds, blurred
    clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds)
    for (cx, cy, cw, chh, alpha) in [
            (300, 300, 330, 16, 55), (700, 380, 260, 13, 48),
            (180, 430, 210, 11, 42), (820, 300, 190, 10, 40)]:
        cd.ellipse([cx - cw / 2, cy - chh / 2, cx + cw / 2, cy + chh / 2],
                   fill=(232, 144, 122, alpha))
    clouds = clouds.filter(ImageFilter.GaussianBlur(14))
    img.paste(Image.alpha_composite(img.convert("RGBA"), clouds).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)

    # ---- ringed planet --------------------------------------------------
    px, py, pr = 720, 205, 82
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    radial_glow(glow, px, py, 190, (245, 217, 160), peak=70)
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)

    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse([px - 165, py - 34, px + 165, py + 34],
               outline=(232, 200, 143, 235), width=9)
    rd.ellipse([px - 165, py - 34, px + 165, py + 34],
               outline=(247, 228, 178, 160), width=3)
    ring = ring.rotate(-18, center=(px, py), resample=Image.BICUBIC)
    # back half of the ring first
    back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    back.paste(ring, (0, 0), ring)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rectangle([0, 0, W, py - 6], fill=255)
    img.paste(Image.alpha_composite(img.convert("RGBA"),
              Image.composite(back, Image.new("RGBA", (W, H), (0, 0, 0, 0)),
                              mask)).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)

    # planet disc with bands
    disc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)
    dd.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(245, 217, 160, 255))
    for (by, bh, col) in [(-38, 10, (226, 186, 128, 220)),
                          (-8, 14, (214, 168, 110, 200)),
                          (26, 9, (232, 196, 140, 210)),
                          (52, 7, (222, 178, 118, 190))]:
        dd.ellipse([px - pr, py + by - bh / 2, px + pr, py + by + bh / 2],
                   fill=col)
    cmask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cmask).ellipse([px - pr, py - pr, px + pr, py + pr],
                                  fill=255)
    disc.putalpha(Image.composite(disc.split()[3], Image.new("L", (W, H), 0),
                                  cmask))
    img.paste(Image.alpha_composite(img.convert("RGBA"), disc).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)
    # front half of the ring over the disc
    fmask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fmask).rectangle([0, py + 6, W, H], fill=255)
    front = Image.composite(ring, Image.new("RGBA", (W, H), (0, 0, 0, 0)),
                            fmask)
    img.paste(Image.alpha_composite(img.convert("RGBA"), front).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)

    # ---- low sun ---------------------------------------------------------
    # big disc low on the horizon, the lighthouse tower stands in front of it
    sx, sy, sr = 512, 598, 86
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    radial_glow(glow, sx, sy, 220, (255, 196, 120), peak=110)
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 217, 138))

    # ---- sea --------------------------------------------------------------
    vgrad(img, 600, 874, [(0.0, SEA_TOP), (0.18, (44, 122, 122)),
                          (0.55, SEA_MID), (1.0, SEA_LOW)])
    d = ImageDraw.Draw(img)

    # sun reflection column: widening gold dashes toward the viewer,
    # jittered and skipped at random so it reads as water, not a ladder
    for i in range(52):
        y = 614 + i * 5.0 + RNG.uniform(-1.5, 1.5)
        if RNG.random() < 0.22:
            continue
        t = i / 51
        half = (12 + t * 92) * RNG.uniform(0.55, 1.0)
        x0 = sx - half + RNG.uniform(-10, 10)
        x1 = sx + half + RNG.uniform(-10, 10)
        alpha = (0.55 - t * 0.3) * RNG.uniform(0.6, 1.0)
        col = tuple(int(lerp(a, b, alpha)) for a, b in
                    zip(lerp_color((255, 205, 120), SEA_MID, t),
                        (255, 205, 120)))
        d.line([(x0, y), (x1, y)], fill=col, width=2)

    # wave strokes
    for _ in range(70):
        y = RNG.uniform(625, 860)
        x = RNG.uniform(40, 984)
        ln = RNG.uniform(18, 95)
        a = RNG.uniform(0.12, 0.4)
        col = lerp_color((190, 230, 225), (20, 96, 107), 1 - a)
        d.line([(x, y), (x + ln, y)], fill=col, width=2)

    # ---- sailboat ---------------------------------------------------------
    bx, by = 305, 742
    d.polygon([(bx - 26, by + 12), (bx + 26, by + 12), (bx + 14, by + 22),
               (bx - 14, by + 22)], fill=(24, 20, 44))
    d.line([(bx, by - 34), (bx, by + 12)], fill=(24, 20, 44), width=3)
    d.polygon([(bx + 2, by - 32), (bx + 2, by + 8), (bx + 30, by + 8)],
              fill=CREAM)
    d.polygon([(bx - 2, by - 26), (bx - 2, by + 8), (bx - 22, by + 8)],
              fill=(232, 214, 178))
    d.line([(bx - 24, by + 28), (bx + 24, by + 28)], fill=(120, 150, 150),
           width=2)

    # ---- islet -------------------------------------------------------------
    isle = [(330, 668), (352, 640), (392, 622), (430, 636), (470, 620),
            (512, 630), (556, 618), (598, 634), (636, 624), (672, 646),
            (692, 668), (512, 668)]
    d.polygon(isle, fill=ROCK)
    # warm rim light along the islet crest
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd2 = ImageDraw.Draw(rim)
    rd2.line(isle[:-1], fill=(255, 190, 110, 150), width=3, joint="curve")
    rim = rim.filter(ImageFilter.GaussianBlur(2))
    img.paste(Image.alpha_composite(img.convert("RGBA"), rim).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)

    # ---- lighthouse: the landmark -----------------------------------------
    base_y, top_y = 668, 396
    cx0 = 512
    left, right = [], []
    for y in range(top_y, base_y + 1, 6):
        t = (y - top_y) / (base_y - top_y)
        half = lerp(15, 26, t)
        sway = 12 * math.sin(math.pi * 0.55 * t)
        left.append((cx0 - half + sway, y))
        right.append((cx0 + half + sway, y))
    tower = left + right[::-1]
    d.polygon(tower, fill=TOWER)
    # cool shadow on the left flank, warm light on the right
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.polygon(left + [(cx0 + 4, base_y), (cx0 + 4, top_y)],
               fill=(90, 70, 130, 90))
    sd.polygon([(cx0 + 8, top_y), (cx0 + 8, base_y)] + right[::-1],
               fill=(255, 200, 120, 70))
    shade = shade.filter(ImageFilter.GaussianBlur(3))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shade).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)
    # coral bands around the tower
    for yy, hh in [(470, 7), (540, 7), (606, 7)]:
        t = (yy - top_y) / (base_y - top_y)
        half = lerp(15, 26, t) - 1
        sway = 12 * math.sin(math.pi * 0.55 * t)
        d.line([(cx0 - half + sway, yy), (cx0 + half + sway, yy)],
               fill=(198, 102, 82), width=hh)
    # gallery deck
    d.polygon([(cx0 - 26, top_y), (cx0 + 26, top_y), (cx0 + 20, top_y - 12),
               (cx0 - 20, top_y - 12)], fill=(42, 33, 64))
    # lantern room with glowing panes
    d.rectangle([cx0 - 15, top_y - 46, cx0 + 15, top_y - 12],
                fill=(30, 24, 52))
    for wx in (-9, 0, 9):
        d.rectangle([cx0 + wx - 3, top_y - 40, cx0 + wx + 3, top_y - 18],
                    fill=LANTERN_GLOW)
    # dome + finial
    d.pieslice([cx0 - 17, top_y - 62, cx0 + 17, top_y - 34], 180, 360,
               fill=(178, 84, 66))
    d.line([(cx0, top_y - 62), (cx0, top_y - 72)], fill=(42, 33, 64), width=3)
    d.ellipse([cx0 - 3, top_y - 76, cx0 + 3, top_y - 70], fill=GOLD)
    # lantern glow + faint beams
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    radial_glow(glow, cx0, top_y - 30, 110, LANTERN_GLOW, peak=130)
    gd = ImageDraw.Draw(glow)
    gd.polygon([(cx0 - 8, top_y - 30), (cx0 - 210, top_y + 110),
                (cx0 - 165, top_y + 165)], fill=(255, 214, 138, 10))
    gd.polygon([(cx0 + 8, top_y - 30), (cx0 + 210, top_y + 110),
                (cx0 + 165, top_y + 165)], fill=(255, 214, 138, 10))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)

    # ---- foreground rocks --------------------------------------------------
    d.polygon([(0, 874), (0, 826), (52, 832), (110, 812), (168, 830),
               (205, 848), (186, 874)], fill=(22, 17, 40))
    d.polygon([(1024, 874), (1024, 830), (972, 836), (916, 816), (862, 834),
               (828, 850), (846, 874)], fill=(22, 17, 40))
    # a few birds
    for (bx2, by2, s) in [(350, 250, 9), (390, 285, 7), (620, 330, 8),
                          (660, 290, 6), (300, 330, 6)]:
        d.line([(bx2 - s, by2), (bx2, by2 - s * 0.6)], fill=(42, 33, 64),
               width=2)
        d.line([(bx2, by2 - s * 0.6), (bx2 + s, by2)], fill=(42, 33, 64),
               width=2)

    # ---- bottom band + name -------------------------------------------------
    d.rectangle([0, 874, W - 1, H - 1], fill=INK)
    d.line([(0, 874), (W - 1, 874)], fill=GOLD, width=3)
    d.line([(0, 882), (W - 1, 882)], fill=(217, 168, 90, 90), width=1)

    try:
        font = ImageFont.truetype(TITLE_FONT, 130)
    except OSError:
        font = ImageFont.truetype(TITLE_FALLBACK, 130)
    # fit the name to the band width
    size = 130
    while tracked_width(font, "VELMORA", 20) > 780 and size > 40:
        size -= 4
        font = ImageFont.truetype(
            TITLE_FONT if Path(TITLE_FONT).exists() else TITLE_FALLBACK, size)
    asc, desc = font.getmetrics()
    text_h = asc + desc
    y_text = 874 + (150 - text_h) // 2
    draw_tracked(d, W // 2, y_text, "VELMORA", font, 20, CREAM,
                 shadow=(10, 13, 32))

    # ---- poster border -------------------------------------------------------
    d.rectangle([22, 22, W - 23, H - 23], outline=(232, 217, 184), width=3)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
