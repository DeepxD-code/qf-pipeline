"""qf_visuals photo backend: AI-photographic backgrounds (Pollinations FLUX,
free, no key) + dark overlay + caption + floating UI panel.

Falls back to gradient cards on any fetch failure — pipeline never breaks.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

from qf_visuals.cards import H, W, _bars, _font, _panel, _progress, _wrap

MODEL = "flux"


def photo_url(visual_prompt: str) -> str:
    q = urllib.parse.quote(f"{visual_prompt}, vertical cinematic photo, no text, no watermark")
    return f"https://image.pollinations.ai/prompt/{q}?width=1080&height=1920&nologo=true&model={MODEL}"


def fetch_photo(visual_prompt: str, out_path: str | Path, timeout: int = 120) -> str:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(photo_url(visual_prompt), headers={"User-Agent": "qf-pipeline/0.1"})
    last: Exception | None = None
    for _ in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r, open(out, "wb") as f:
                f.write(r.read())
            Image.open(out).verify()
            return str(out)
        except Exception as exc:
            last = exc
    raise RuntimeError(f"photo fetch failed for {visual_prompt!r}: {last}")


def render_photo_cards(script, out_dir: str | Path) -> list[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    n = len(script.scenes)
    widgets = ["player", "stats", "cta"]
    for i, scene in enumerate(script.scenes):
        bg_path = out / f"bg_{i + 1:02d}.jpg"
        fetch_photo(scene.visual_prompt, bg_path)
        img = Image.open(bg_path).convert("RGB").resize((W, H))
        dim = Image.new("RGB", (W, H), (5, 5, 10))
        img = Image.blend(img, dim, 0.45)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([60, 90, 400, 170], radius=24, fill=(255, 255, 255))
        d.text((90, 108), f"QONEQT  {i + 1}/{n}", font=_font(40), fill=(20, 20, 30))
        lines = _wrap(d, scene.caption, _font(104), W - 160)[:3]
        y = 260
        for k, line in enumerate(lines):
            fill = (255, 255, 255) if k < len(lines) - 1 or len(lines) == 1 else (230, 230, 240)
            d.text((80, y), line, font=_font(104), fill=fill)
            y += 132
        kind = widgets[i % len(widgets)]
        px, py, pw, ph = 110, 760, W - 220, 560
        _panel(d, (px, py, px + pw, py + ph))
        if kind == "player":
            vo = scene.voiceover
            if len(vo) > 64:
                vo = vo[:64].rsplit(" ", 1)[0]
            d.text((px + 50, py + 44), scene.title.upper(), font=_font(38), fill=(255, 255, 255))
            d.text((px + 50, py + 110), vo, font=_font(30, False), fill=(255, 235, 120))
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
            d.rounded_rectangle([px + 50, py + 380, px + pw - 50, py + 480], radius=50, fill=(255, 235, 120))
            d.text((px + 110, py + 408), "Post it on Qoneqt", font=_font(40), fill=(20, 20, 30))
        d.text((80, H - 160), "Qoneqt Global Feed  9:16", font=_font(36, False), fill=(220, 220, 230))
        p = out / f"scene_{i + 1:02d}.png"
        img.save(p)
        paths.append(str(p))
    return paths
