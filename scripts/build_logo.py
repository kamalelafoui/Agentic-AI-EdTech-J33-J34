# -*- coding: utf-8 -*-
"""Crée l'identité visuelle EduAgentic (logo horizontal, marque, favicon)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

NAVY = (11, 35, 64, 255)
NAVY_2 = (20, 54, 92, 255)
GOLD = (244, 180, 0, 255)
TEAL = (22, 166, 161, 255)
WHITE = (255, 255, 255, 255)
MUTED = (122, 140, 166, 255)

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"
FONT_SEMI = "C:/Windows/Fonts/seguisb.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)


def draw_mark(size: int = 720) -> Image.Image:
    scale = 2
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(s * 0.035)
    radius = int(s * 0.23)
    # fond arrondi avec dégradé simulé
    d.rounded_rectangle((pad, pad, s - pad, s - pad), radius=radius, fill=NAVY)
    d.rounded_rectangle(
        (pad, pad, s - pad, int(s * 0.56)), radius=radius, fill=(15, 45, 78, 255)
    )
    # halo
    d.ellipse(
        (int(s * 0.18), int(s * 0.18), int(s * 0.82), int(s * 0.82)),
        outline=(244, 180, 0, 40),
        width=int(s * 0.045),
    )
    # noeuds réseau (3 agents) + liens
    cx, cy = s // 2, int(s * 0.31)
    r = int(s * 0.038)
    nodes = [(int(s * 0.30), int(s * 0.40)), (cx, int(s * 0.19)), (int(s * 0.70), int(s * 0.40))]
    for nx, ny in nodes:
        d.line((cx, cy, nx, ny), fill=(244, 180, 0, 150), width=int(s * 0.012))
    for nx, ny in nodes:
        d.ellipse((nx - r, ny - r, nx + r, ny + r), fill=TEAL if nx == cx else GOLD)
    d.ellipse((cx - int(r * 1.25), cy - int(r * 1.25), cx + int(r * 1.25), cy + int(r * 1.25)), fill=WHITE)
    # livre ouvert
    top = int(s * 0.50)
    bottom = int(s * 0.76)
    mid = s // 2
    left = (int(s * 0.19), top + int(s * 0.10))
    right = (int(s * 0.81), top + int(s * 0.10))
    d.polygon(
        [
            (left[0], left[1] + int(s * 0.02)),
            (mid - int(s * 0.02), top),
            (mid - int(s * 0.02), bottom),
            (left[0], bottom + int(s * 0.04)),
        ],
        fill=WHITE,
    )
    d.polygon(
        [
            (right[0], right[1] + int(s * 0.02)),
            (mid + int(s * 0.02), top),
            (mid + int(s * 0.02), bottom),
            (right[0], bottom + int(s * 0.04)),
        ],
        fill=(229, 240, 251, 255),
    )
    d.line((mid, top + int(s * 0.01), mid, bottom), fill=GOLD, width=int(s * 0.014))
    # lignes de texte stylisées
    for i in range(3):
        y = int(s * 0.60) + i * int(s * 0.05)
        d.rounded_rectangle(
            (int(s * 0.27), y, int(s * 0.44), y + int(s * 0.017)),
            radius=int(s * 0.01),
            fill=(180, 205, 228, 255),
        )
        d.rounded_rectangle(
            (int(s * 0.56), y, int(s * 0.73), y + int(s * 0.017)),
            radius=int(s * 0.01),
            fill=(180, 205, 228, 255),
        )
    # point d'accent
    d.ellipse(
        (int(s * 0.74), int(s * 0.72), int(s * 0.82), int(s * 0.80)),
        fill=GOLD,
    )
    return img.resize((size, size), Image.LANCZOS)


def draw_wordmark(dark: bool = True, width: int = 1600, height: int = 420) -> Image.Image:
    scale = 2
    W, H = width * scale, height * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mark = draw_mark(int(H * 0.80))
    img.alpha_composite(mark, (int(H * 0.06), int(H * 0.10)))
    d = ImageDraw.Draw(img)
    x = int(H * 0.94)
    main = WHITE if dark else NAVY
    f1 = font(FONT_BOLD, int(H * 0.255))
    f2 = font(FONT_BOLD, int(H * 0.255))
    f3 = font(FONT_SEMI, int(H * 0.074))
    f4 = font(FONT_REG, int(H * 0.054))
    # Edu + Agentic
    d.text((x, int(H * 0.145)), "Edu", font=f1, fill=main)
    edu_w = d.textlength("Edu", font=f1)
    d.text((x + edu_w, int(H * 0.145)), "Agentic", font=f2, fill=GOLD)
    d.text((x + 2, int(H * 0.520)), "AGENTIC AI FOR EDUCATION", font=f3, fill=TEAL)
    d.text(
        (x + 2, int(H * 0.645)),
        "MCP · A2A · Jours 33 & 34 · v1.0",
        font=f4,
        fill=(185, 204, 224) if dark else MUTED,
    )
    # fine ligne d'accent
    d.rounded_rectangle(
        (x, int(H * 0.815), x + int(H * 0.38), int(H * 0.815) + 3),
        radius=2,
        fill=GOLD,
    )
    return img.resize((width, height), Image.LANCZOS)


def draw_sidebar_logo(width: int = 1200, height: int = 320) -> Image.Image:
    """Version compacte pour la barre latérale sombre du dashboard."""
    scale = 2
    W, H = width * scale, height * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mark = draw_mark(int(H * 0.82))
    img.alpha_composite(mark, (int(H * 0.04), int(H * 0.09)))
    d = ImageDraw.Draw(img)
    x = int(H * 0.98)
    f1 = font(FONT_BOLD, int(H * 0.34))
    f2 = font(FONT_BOLD, int(H * 0.34))
    d.text((x, int(H * 0.19)), "Edu", font=f1, fill=WHITE)
    edu_w = d.textlength("Edu", font=f1)
    d.text((x + edu_w, int(H * 0.19)), "Agentic", font=f2, fill=GOLD)
    f3 = font(FONT_SEMI, int(H * 0.10))
    d.text((x + 3, int(H * 0.63)), "MCP  ·  A2A", font=f3, fill=TEAL)
    return img.resize((width, height), Image.LANCZOS)


def main() -> None:
    mark = draw_mark(640)
    mark.save(ASSETS / "logo_mark.png")
    mark.resize((128, 128), Image.LANCZOS).save(ASSETS / "favicon.png")
    draw_wordmark(dark=True, width=1600, height=420).save(ASSETS / "logo.png")
    draw_wordmark(dark=False, width=1600, height=420).save(ASSETS / "logo_light.png")
    draw_sidebar_logo().save(ASSETS / "logo_sidebar.png")
    # variante compacte pour PowerPoint / docs
    draw_wordmark(dark=False, width=1100, height=290).save(ASSETS / "logo_small.png")
    print("Logos générés dans", ASSETS)


if __name__ == "__main__":
    main()
