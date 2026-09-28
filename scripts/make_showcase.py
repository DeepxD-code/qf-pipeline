"""Compress showcase MP4s for web delivery and grab poster frames.

Run: python scripts/make_showcase.py
Writes: apps/web/media/<slug>.mp4 (web-optimised) + <slug>.jpg (poster)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "storage" / "videos"
OUT = ROOT / "apps" / "web" / "media"

# (source file, slug, label) - the four distinct 22s copy-mode renders,
# written by scripts/render_showcase.py (cinema is the earlier hand-tuned pass).
SHOWCASE = [
    ("show-chai.mp4", "chai", "Chai tapri sunrise regulars"),
    ("show-keyboard.mp4", "keyboard", "Mechanical keyboard custom build"),
    ("show-maggi.mp4", "maggi", "Maggi instant noodles review"),
    ("copy5-final.mp4", "cinema", "Chai tapri - cinema grade"),
]


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for src_name, slug, _label in SHOWCASE:
        src = SRC / src_name
        if not src.exists():
            print(f"skip {src_name}: not found", file=sys.stderr)
            continue
        dest = OUT / f"{slug}.mp4"
        # 720x1280 is plenty for a web grid, keeps 1080x1920 aspect for feed proof.
        run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
            "-vf", "scale=720:1280",
            "-c:v", "libx264", "-preset", "slow", "-crf", "30",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "96k",
            str(dest),
        ])
        # Poster from a settled frame (~2s in, past the hook fade).
        run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", "2.0",
            "-i", str(src), "-frames:v", "1", "-q:v", "4",
            str(OUT / f"{slug}.jpg"),
        ])
        mb = dest.stat().st_size / 1e6
        print(f"  {slug}.mp4  {mb:.2f} MB", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
