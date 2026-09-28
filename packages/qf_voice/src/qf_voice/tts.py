"""qf_voice: free Edge-TTS voiceover, timed to scenes. Silent fallback."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

VOICE = "en-US-GuyNeural"


def _have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def synthesize(text: str, out_mp3: str | Path, voice: str = VOICE) -> str:
    """One TTS line. Raises on any failure (caller decides fallback)."""
    import edge_tts

    out = Path(out_mp3)
    out.parent.mkdir(parents=True, exist_ok=True)

    async def _run() -> None:
        await edge_tts.Communicate(text, voice).save(str(out))

    asyncio.run(_run())
    if not out.exists() or out.stat().st_size < 1000:
        raise RuntimeError("edge-tts produced no audio")
    return str(out)


def build_voiceover(script, out_dir: str | Path, secs_per_image: float, voice: str = VOICE) -> str | None:
    """Per-scene MP3s delayed to scene starts, mixed + padded to total. None on failure."""
    try:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        total = round(len(script.scenes) * secs_per_image, 3)
        parts: list[Path] = []
        for i, scene in enumerate(script.scenes):
            p = out / f"vo_{i + 1:02d}.mp3"
            synthesize(scene.voiceover, p, voice)
            parts.append(p)
        mixed = out / "voiceover.mp3"
        cmd = ["ffmpeg", "-y"]
        for p in parts:
            cmd += ["-i", str(p)]
        fc, maps = [], []
        for i in range(len(parts)):
            start_ms = int(round(i * secs_per_image * 1000))
            fc.append(f"[{i}:a]adelay={start_ms}|{start_ms}[d{i}]")
            maps.append(f"[d{i}]")
        fc.append(f"{''.join(maps)}amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{total}[v]")
        cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-c:a", "libmp3lame", str(mixed)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if p.returncode != 0 or not mixed.exists():
            return None
        return str(mixed)
    except Exception:
        return None
