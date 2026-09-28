"""qf_audio: full mix — voiceover + music bed + brag SFX hits. All graceful."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SFX = ROOT / "brag-assets" / "sfx"
MUSIC = ROOT / "brag-assets" / "music" / "happy-beats-business-moves-vol-1-by-ende-dot-app.mp3"


def _ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def scene_sfx_events(n_scenes: int, scene_step: float) -> list[tuple[float, str, float]]:
    """(time_s, file, volume) hits for hard beat cuts."""
    events: list[tuple[float, str, float]] = [(0.15, "impact/impactBell_heavy_000.ogg", 0.8)]
    cuts = ["interface/switch_004.ogg", "interface/switch_006.ogg", "interface/drop_003.ogg"]
    for i in range(1, n_scenes):
        events.append((round(i * scene_step, 3), cuts[(i - 1) % len(cuts)], 0.7))
    events.append((round((n_scenes - 1) * scene_step + 0.4, 3), "impact/impactSoft_medium_000.ogg", 0.7))
    return [(t, f, v) for t, f, v in events if (SFX / f).exists()]


def build_sfx_track(events: list[tuple[float, str, float]], total: float, out_path: str | Path) -> str | None:
    try:
        if not events or not _ffmpeg():
            return None
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["ffmpeg", "-y"]
        for _, f, _ in events:
            cmd += ["-i", str(SFX / f)]
        fc, maps = [], []
        for i, (t, _, v) in enumerate(events):
            ms = int(round(t * 1000))
            fc.append(f"[{i}:a]adelay={ms}|{ms},volume={v}[s{i}]")
            maps.append(f"[s{i}]")
        fc.append(f"{''.join(maps)}amix=inputs={len(events)}:normalize=0,apad,atrim=0:{total}[m]")
        cmd += ["-filter_complex", ";".join(fc), "-map", "[m]", "-c:a", "libmp3lame", str(out)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return str(out) if p.returncode == 0 and out.exists() else None
    except Exception:
        return None


def mix_final(
    video_noaudio: str | Path,
    voice_mp3: str | Path | None,
    music_path: str | Path | None,
    sfx_mp3: str | Path | None,
    total: float,
    out_mp4: str | Path,
    music_vol: float = 0.18,
) -> str:
    """Mux voice + music bed + sfx hits under video. Falls back to plain copy."""
    out = Path(out_mp4)
    exe = _ffmpeg()
    inputs: list[str] = []
    if voice_mp3 and Path(voice_mp3).exists():
        inputs.append(("voice", str(voice_mp3), "1.0"))
    if music_path and Path(music_path).exists():
        inputs.append(("music", str(music_path), str(music_vol)))
    if sfx_mp3 and Path(sfx_mp3).exists():
        inputs.append(("sfx", str(sfx_mp3), "1.0"))
    if not exe or not inputs:
        if str(video_noaudio) != str(out):
            shutil.copyfile(video_noaudio, out)
        return str(out)
    try:
        cmd = [exe, "-y", "-i", str(video_noaudio)]
        for _, f, _ in inputs:
            cmd += ["-i", f]
        fc, maps = [], []
        for i, (kind, _, vol) in enumerate(inputs, start=1):
            if kind == "music":
                fade_st = round(max(0.0, total - 1), 3)
                fc.append(
                    f"[{i}:a]atrim=0:{total},asetpts=PTS-STARTPTS,volume={vol},"
                    f"afade=t=out:st={fade_st}:d=1[{kind}]"
                )
            else:
                fc.append(f"[{i}:a]atrim=0:{total},asetpts=PTS-STARTPTS,volume={vol}[{kind}]")
            maps.append(f"[{kind}]")
        n = len(maps)
        if n == 1:
            amap = maps[0]
        else:
            fc.append(f"{''.join(maps)}amix=inputs={n}:normalize=0[m]")
            amap = "[m]"
        cmd += ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", amap,
                "-c:v", "copy", "-c:a", "aac", "-t", str(total), str(out)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if p.returncode != 0 or not out.exists():
            shutil.copyfile(video_noaudio, out)
        return str(out)
    except Exception:
        shutil.copyfile(video_noaudio, out)
        return str(out)
