"""qf_compose: cinematic slideshow — Ken Burns drift + xfade cuts + optional bed.

Every frame moves (slow zoom in/out alternating per scene) and scenes melt
into each other instead of hard-cutting. Optional QF_MUSIC bed muxed under.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg not found on PATH (apt: ffmpeg / choco: ffmpeg / docker image has it)")
    return exe


def _zoom_expr(i: int, frames: int) -> str:
    # Alternate push-in / pull-out per scene so cuts feel motivated.
    return f"1+0.15*on/{frames}" if i % 2 == 0 else f"1.15-0.15*on/{frames}"


def compose_slideshow(
    images: list[str],
    out_mp4: str | Path,
    secs_per_image: float = 2.5,
    fps: int = 30,
    xfade: float = 0.5,
    music: str | Path | None = None,
    music_fade: bool = True,
) -> str:
    exe = _ffmpeg()
    out = Path(out_mp4)
    out.parent.mkdir(parents=True, exist_ok=True)
    music = music or os.getenv("QF_MUSIC", "").strip() or None
    frames = max(1, int(secs_per_image * fps))
    with tempfile.TemporaryDirectory() as td:
        segs: list[Path] = []
        for i, img in enumerate(images):
            seg = Path(td) / f"seg_{i:02d}.mp4"
            vf = (
                "scale=2160:3840,"
                f"zoompan=z='{_zoom_expr(i, frames)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s=1080x1920:fps={fps},format=yuv420p"
            )
            cmd = [
                exe,
                "-y",
                "-loop",
                "1",
                "-framerate",
                str(fps),
                "-i",
                img,
                "-vf",
                vf,
                "-t",
                str(secs_per_image),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                str(seg),
            ]
            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                raise RuntimeError(f"ffmpeg segment {i} failed: {(p.stderr or '')[-2000:]}")
            segs.append(seg)
        # xfade chain: offset_k melts each next scene into the running cut.
        if len(segs) == 1:
            final = segs[0]
            chained = Path(td) / "chained.mp4"
            shutil.copyfile(final, chained)
        else:
            cmd = [exe, "-y"]
            for s in segs:
                cmd += ["-i", str(s)]
            cur, fc = "[0:v]", []
            dur = secs_per_image
            for k in range(1, len(segs)):
                nxt, off = f"[x{k}]", round(dur - xfade, 3)
                fc.append(f"{cur}[{k}:v]xfade=transition=fade:duration={xfade}:offset={off}{nxt}")
                cur, dur = nxt, round(dur + secs_per_image - xfade, 3)
            cmd += [
                "-filter_complex",
                ";".join(fc),
                "-map",
                cur,
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                str(Path(td) / "chained.mp4"),
            ]
            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                raise RuntimeError(f"ffmpeg xfade failed: {(p.stderr or '')[-2000:]}")
            chained = Path(td) / "chained.mp4"
        if music and Path(music).exists():
            total = dur if len(segs) > 1 else secs_per_image
            afade = f",afade=t=out:st={round(total - 1, 3)}:d=1" if music_fade else ""
            cmd = [
                exe,
                "-y",
                "-i",
                str(chained),
                "-i",
                str(music),
                "-filter_complex",
                f"[1:a]atrim=0:{total},asetpts=PTS-STARTPTS{afade}[a]",
                "-map",
                "0:v",
                "-map",
                "[a]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-t",
                str(total),
                str(out),
            ]
            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                raise RuntimeError(f"ffmpeg music mux failed: {(p.stderr or '')[-2000:]}")
        else:
            shutil.copyfile(chained, out)
    return str(out)
