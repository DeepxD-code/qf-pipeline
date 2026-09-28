"""qf_compose java backend: delegate to workers/java-renderer (pure JDK 21, no deps).

Why Java here: the composer shells ffmpeg either way (native code does the
heavy lifting), so Python-vs-Java CPU is a wash per encode. The win is
operational: a bounded, low-memory JVM worker with virtual threads + a
Semaphore(2) cap, so a burst of topics can't fork-bomb ffmpeg. Falls back to
the Python composer when java/javac output is unavailable.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _worker_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "workers" / "java-renderer"
        if (candidate / "src" / "Compose.java").exists():
            return candidate
    return Path(__file__).resolve().parents[4] / "workers" / "java-renderer"


WORKER = _worker_dir()


def _java() -> str:
    exe = shutil.which("java")
    if not exe:
        raise RuntimeError("java not found on PATH (need JDK 21+ for QF_COMPOSER=java)")
    return exe


def _classes_dir() -> Path:
    d = WORKER / "classes"
    if not (d / "Compose.class").exists():
        raise RuntimeError("Java renderer not built — run workers/java-renderer/build.bat first")
    return d


def compose_java(images: list[str], out_mp4: str | Path, secs_per_image: float = 2.5, fps: int = 30) -> str:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        lst = Path(td) / "images.txt"
        lst.write_text("\n".join(images))
        cmd = [
            _java(),
            "-cp",
            str(_classes_dir()),
            "Compose",
            str(lst),
            str(out_mp4),
            str(secs_per_image),
            str(fps),
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if p.returncode != 0 or not Path(out_mp4).exists():
            raise RuntimeError(f"java Compose failed: {((p.stderr or '') + (p.stdout or ''))[-2000:]}")
    return str(out_mp4)
