"""Render the showcase set through the current copy pipeline.

Each topic is rendered with the topic-driven beat set and the style chosen by
hash, so the four showcase clips are genuinely distinct and current.

Run: python scripts/render_showcase.py
Writes: storage/videos/show-<slug>.mp4  (22s, 1080x1920, h264 + aac)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qf_visuals.copy import build_copy, choose_style, style_music  # noqa: E402
from qf_visuals.hyperframes import render_composition  # noqa: E402

from qf_script import template_script  # noqa: E402

OUT = ROOT / "storage" / "videos"
COMPS = ROOT / "storage" / "comps"

# (slug, topic) - cinema/chai is already rendered (copy5-final.mp4)
TOPICS = [
    ("chai", "Chai tapri sunrise regulars"),
    ("keyboard", "Mechanical keyboard custom build"),
    ("maggi", "Maggi instant noodles review"),
]

CUTS = [3.1, 6.6, 10.1, 13.6, 17.1]
CUT_SFX = [
    "interface/switch_004.ogg",
    "interface/switch_006.ogg",
    "interface/drop_003.ogg",
]


def main() -> int:
    from qf_audio import build_sfx_track, mix_final

    OUT.mkdir(parents=True, exist_ok=True)
    for slug, topic in TOPICS:
        style = choose_style(topic)
        print(f"\n=== {slug}: {topic!r} (style={style}) ===", flush=True)
        comp_dir = COMPS / f"show-{slug}"
        script = template_script(topic)
        comp = build_copy(script, comp_dir, style=style)

        raw = OUT / f"show-{slug}.raw.mp4"
        dest = OUT / f"show-{slug}.mp4"
        render_composition(comp, str(raw))

        ev: list[tuple[float, str, float]] = [(0.15, "impact/impactBell_heavy_000.ogg", 0.5)]
        for k, cut in enumerate(CUTS):
            ev.append((cut, CUT_SFX[k % len(CUT_SFX)], 0.7))
        ev += [
            (17.3, "impact/impactBell_heavy_000.ogg", 0.8),
            (21.0, "impact/impactSoft_medium_000.ogg", 0.7),
        ]
        sfx = build_sfx_track(ev, 22.0, comp_dir / "sfx.mp3")
        music = style_music(style)
        mix_final(
            str(raw), None, str(music) if music.exists() else None, sfx,
            22.0, str(dest), music_vol=0.4,
        )
        raw.unlink(missing_ok=True)
        print(f"  -> {dest.name}  {dest.stat().st_size / 1e6:.2f} MB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
