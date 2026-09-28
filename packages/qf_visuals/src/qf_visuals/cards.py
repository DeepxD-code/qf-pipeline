"""qf_visuals: cinematic 1080x1920 cards — glow orb + floating UI panel + captions.

Reference style (user-supplied Qoneqt-grade promo): near-black background,
blue glow horizon, one floating product-UI card in perspective, one punchy
caption. No generic gradient washes.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920


_FONTS_TTL = {}


def _font(size: int, bold: bool = True):
    key = (size, bold)
    if key not in _FONTS_TTL:
        names = (
            ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial_Bold.ttf"]
            if bold
            else ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf"]
        )
        for name in names:
            try:
                _FONTS_TTL[key] = ImageFont.truetype(name, size)
                break
            except Exception:
                continue
        else:
            _FONTS_TTL[key] = ImageFont.load_default()
    return _FONTS_TTL[key]


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _glow(base: Image.Image, cx: int, cy: int, rx: int, ry: int) -> None:
    """Radial blue glow: concentric ellipses, fading alpha."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 40
    for i in range(steps, 0, -1):
        f = i / steps
        alpha = int(110 * (1 - f) ** 2)
        d.ellipse([cx - rx * f, cy - ry * f, cx + rx * f, cy + ry * f], fill=(40, 90, 220, alpha))
    base.alpha_composite(layer)


def _panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=36, fill=(21, 21, 31), outline=(42, 42, 58), width=3)


def _progress(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, frac: float) -> None:
    draw.rounded_rectangle([x, y, x + w, y + 14], radius=7, fill=(50, 50, 66))
    draw.rounded_rectangle([x, y, x + int(w * frac), y + 14], radius=7, fill=(255, 235, 120))


def _bars(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, rows: list[tuple[str, float]]) -> int:
    for label, frac in rows:
        draw.text((x, y), label, font=_font(30, False), fill=(200, 200, 210))
        y += 44
        draw.rounded_rectangle([x, y, x + w, y + 22], radius=11, fill=(50, 50, 66))
        draw.rounded_rectangle([x, y, x + int(w * frac), y + 22], radius=11, fill=(120, 220, 140))
        y += 58
    return y


def render_cards(script, out_dir: str | Path) -> list[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    n = len(script.scenes)
    widgets = ["player", "stats", "cta"]
    for i, scene in enumerate(script.scenes):
        img = Image.new("RGBA", (W, H), (11, 11, 18, 255))
        _glow(img, W // 2, 1250, 750, 460)
        d = ImageDraw.Draw(img)
        # top badge
        d.rounded_rectangle([60, 90, 400, 170], radius=24, fill=(255, 255, 255))
        d.text((90, 108), f"QONEQT  {i + 1}/{n}", font=_font(40), fill=(20, 20, 30))
        # caption (big, punchy — last line dim like the reference)
        lines = _wrap(d, scene.caption, _font(104), W - 160)[:3]
        y = 260
        for k, line in enumerate(lines):
            fill = (255, 255, 255) if k < len(lines) - 1 or len(lines) == 1 else (150, 150, 165)
            d.text((80, y), line, font=_font(104), fill=fill)
            y += 132
        # floating UI panel (center)
        kind = widgets[i % len(widgets)]
        px, py, pw, ph = 110, 760, W - 220, 560
        _panel(d, (px, py, px + pw, py + ph))
        if kind == "player":
            d.text((px + 50, py + 44), scene.title.upper(), font=_font(38), fill=(255, 255, 255))
            d.text((px + 50, py + 110), scene.voiceover[:64], font=_font(30, False), fill=(255, 235, 120))
            _progress(d, px + 50, py + 200, pw - 100, 0.35 + 0.2 * i)
            d.text((px + 50, py + 240), "0:47", font=_font(28, False), fill=(160, 160, 175))
            d.text((px + pw - 140, py + 240), "2:30", font=_font(28, False), fill=(160, 160, 175))
            d.ellipse([px + pw // 2 - 55, py + 320, px + pw // 2 + 55, py + 430], fill=(255, 235, 120))
            d.polygon(
                [(px + pw // 2 - 18, py + 345), (px + pw // 2 - 18, py + 405), (px + pw // 2 + 28, py + 375)],
                fill=(20, 20, 30),
            )
        elif kind == "stats":
            d.text((px + 50, py + 44), scene.title.upper(), font=_font(38), fill=(255, 255, 255))
            _bars(d, px + 50, py + 130, pw - 100, [("HOOK RATE", 0.43 + 0.1 * i), ("WATCH TIME", 0.52 + 0.08 * i)])
            d.text((px + 50, py + 420), "Qoneqt Global Feed", font=_font(30, False), fill=(160, 160, 175))
        else:
            d.text((px + 50, py + 60), scene.title.upper(), font=_font(40), fill=(255, 255, 255))
            _wrap(d, scene.caption, _font(34, False), pw - 120)
            d.rounded_rectangle([px + 50, py + 380, px + pw - 50, py + 480], radius=50, fill=(255, 235, 120))
            d.text((px + 110, py + 408), "Post it on Qoneqt", font=_font(40), fill=(20, 20, 30))
        # footer
        d.text((80, H - 160), "Qoneqt Global Feed  9:16", font=_font(36, False), fill=(200, 200, 210))
        p = out / f"scene_{i + 1:02d}.png"
        img.convert("RGB").save(p)
        paths.append(str(p))
    return paths
