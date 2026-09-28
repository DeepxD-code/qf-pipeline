"""Render one MP4 without running the server.

Usage:
  python scripts/render_sample.py --topic "..." [--visuals cards|photo] [--voice|--no-voice]
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api/src"))
sys.path.insert(0, str(ROOT / "packages/qf_script/src"))
sys.path.insert(0, str(ROOT / "packages/qf_visuals/src"))
sys.path.insert(0, str(ROOT / "packages/qf_compose/src"))
sys.path.insert(0, str(ROOT / "packages/qf_voice/src"))

from qf_visuals.photo import render_photo_cards  # noqa: E402

from qf_compose import compose_slideshow  # noqa: E402
from qf_script import generate_script  # noqa: E402
from qf_visuals import render_cards  # noqa: E402
from qf_voice import build_voiceover  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="AI communities in Kochi")
    ap.add_argument("--out", default="storage/videos/sample.mp4")
    ap.add_argument("--visuals", default=os.getenv("QF_VISUALS", "cards"), choices=["cards", "photo"])
    ap.add_argument("--voice", dest="voice", action="store_true", default=os.getenv("QF_VOICE", "1") == "1")
    ap.add_argument("--no-voice", dest="voice", action="store_false")
    args = ap.parse_args()
    script = generate_script(args.topic)
    if args.visuals == "photo":
        try:
            cards = render_photo_cards(script, "storage/cards/sample")
        except Exception as exc:
            print(f"photo backend failed, falling back to cards: {exc}")
            cards = render_cards(script, "storage/cards/sample")
    else:
        cards = render_cards(script, "storage/cards/sample")
    voice = build_voiceover(script, "storage/cards/sample", 2.5) if args.voice else None
    if args.voice and not voice:
        print("voiceover unavailable, continuing silent")
    out = compose_slideshow(cards, args.out, music=voice, music_fade=False)
    print(f"wrote {out}")
    print(f"hook: {script.hook}")


if __name__ == "__main__":
    main()
