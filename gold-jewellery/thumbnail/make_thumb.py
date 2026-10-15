"""Put The Long Story thumbnail text on a 1280x720 image.

Same style as the gold video ("Older Than Earth"): big white bold serif, top-left,
with a red underline under one word.

  python make_thumb.py --bg flow_image.png --line1 "6,000 Years" --line2 "Old" --underline "6,000" --out thumb.png
  python make_thumb.py --line1 ...   # no --bg: draws a placeholder gold bangle on black
"""
import argparse
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
FONT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
RED = (224, 27, 27)


def placeholder_bg():
    """Black background, gold sparks, a glowing gold bangle on the right."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy, rx, ry = 860, 400, 330, 210
    r = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    ang = np.arctan2(y - cy, x - cx)
    band = np.clip(1 - np.abs(r - 1) / 0.13, 0, 1)
    shade = 0.55 + 0.45 * np.cos(ang * 2 + 0.8) ** 2
    spec = np.clip(1 - np.abs(r - 0.97) / 0.025, 0, 1) * np.clip(np.cos(ang + 2.2), 0, 1) ** 4
    gold = np.stack([255 * shade, 190 * shade, 70 * shade], -1)
    img = gold * band[..., None] ** 0.6 + 255 * spec[..., None]
    glow = np.exp(-((r - 1) ** 2) / 0.08)[..., None] * np.array([120, 70, 10]) * 0.35
    vign = np.exp(-(((x - cx) / 700) ** 2 + ((y - cy) / 500) ** 2))[..., None] * np.array([40, 22, 5])
    base = Image.fromarray(np.clip(img + glow + vign, 0, 255).astype(np.uint8))
    sparks = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(sparks)
    rnd = random.Random(7)
    for _ in range(260):
        a = rnd.uniform(0, 2 * math.pi)
        dist = rnd.uniform(0.6, 2.4)
        px, py = cx + math.cos(a) * rx * dist, cy + math.sin(a) * ry * dist
        s = rnd.choice([1, 1, 2, 2, 3])
        c = rnd.randint(140, 255)
        d.ellipse([px - s, py - s, px + s, py + s], fill=(c, int(c * 0.65), int(c * 0.2)))
    sparks = Image.blend(sparks, sparks.filter(ImageFilter.GaussianBlur(2)), 0.5)
    return Image.fromarray(np.clip(np.asarray(base, np.int32) + np.asarray(sparks, np.int32), 0, 255).astype(np.uint8))


def cover(img):
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    left, top = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


def draw_text(img, lines, underline, size, x0=40, y0=36, gap=1.2):
    font = ImageFont.truetype(FONT, size)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    top = ImageDraw.Draw(img)
    y = y0
    for line in lines:
        sd.text((x0 + 4, y + 5), line, font=font, fill=(0, 0, 0, 230))
        top_y = y
        y += int(size * gap)
        if underline and underline in line:
            pre = line[: line.index(underline)]
            ux0 = x0 + top.textlength(pre, font=font)
            ux1 = ux0 + top.textlength(underline, font=font)
            uy = top_y + int(size * 1.0)
            line_rect = [ux0 - 2, uy, ux1 + 2, uy + max(6, size // 16)]
            sd.rectangle([r + o for r, o in zip(line_rect, (3, 4, 3, 4))], fill=(0, 0, 0, 200))
            draw_text.rects.append(line_rect)
    img.paste(Image.alpha_composite(img.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(6))).convert("RGB"))
    top = ImageDraw.Draw(img)
    y = y0
    for line in lines:
        top.text((x0, y), line, font=font, fill="white")
        y += int(size * gap)
    for rect in draw_text.rects:
        top.rectangle(rect, fill=RED)
    draw_text.rects = []
    return img


draw_text.rects = []

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg")
    ap.add_argument("--line1", required=True)
    ap.add_argument("--line2", default="")
    ap.add_argument("--underline", default="")
    ap.add_argument("--size", type=int, default=118)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bg = cover(Image.open(a.bg).convert("RGB")) if a.bg else placeholder_bg()
    lines = [l for l in (a.line1, a.line2) if l]
    draw_text(bg, lines, a.underline, a.size).save(a.out, quality=95)
    print(a.out)
