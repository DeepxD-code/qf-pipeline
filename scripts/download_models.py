"""Resumable, retrying model downloader.

Runs detached from the agent session so a session/server restart cannot kill a
multi-hour transfer. Two things this fixes versus a bare snapshot_download:

1. Per-file retry with backoff. The 6 diffusion shards are ~9.5 GB each; a single
   network blip on a 40 GB pull should not restart the whole thing.
2. Xet disabled. The Xet CAS backend failed twice with
   "File reconstruction error ... error decoding response body"; plain HTTP with
   Range resume is reliable here.

Usage:
    python scripts/download_models.py
    WAN_DIR=/mnt/models python scripts/download_models.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# (hf repo id, path relative to BASE_DIR)
REPOS = [
    ("Wan-AI/Wan2.1-T2V-14B", "models/Wan2.1-T2V-14B"),
    ("HeyGenAI/TransVLM-Qwen3-VL-4B-Instruct", "heygen/TransVLM/pretrained/TransVLM-v1"),
]

MAX_ATTEMPTS = 8
BASE_DIR = Path(os.environ.get("WAN_DIR", r"E:\Potential-gold"))


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def total_gb(root: Path) -> float:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file()) / 1e9


def fetch(repo_id: str, local_dir: Path) -> None:
    from huggingface_hub import snapshot_download

    local_dir.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            log(f"{repo_id}: attempt {attempt}/{MAX_ATTEMPTS}")
            path = snapshot_download(
                repo_id,
                local_dir=str(local_dir),
                max_workers=2,
                resume_download=True,
            )
        except Exception as exc:  # noqa: BLE001 - retry on anything transient
            wait = min(60, 5 * attempt)
            log(f"{repo_id}: failed ({type(exc).__name__}: {str(exc)[:160]})")
            if attempt == MAX_ATTEMPTS:
                log(f"{repo_id}: GIVING UP after {MAX_ATTEMPTS} attempts")
                raise
            log(f"{repo_id}: retrying in {wait}s")
            time.sleep(wait)
        else:
            log(f"{repo_id}: COMPLETE -> {path}")
            return


def main() -> int:
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    failed: list[str] = []
    for repo_id, rel in REPOS:
        dest = BASE_DIR / rel
        log(f"=== {repo_id} -> {dest}")
        try:
            fetch(repo_id, dest)
        except Exception as exc:  # noqa: BLE001 - report, keep going
            failed.append(f"{repo_id}: {exc}")

    log("--- summary ---")
    for _repo_id, rel in REPOS:
        log(f"{rel}: {total_gb(BASE_DIR / rel):.2f} GB")

    if failed:
        log("INCOMPLETE:")
        for f in failed:
            log("  " + f)
        return 1
    log("ALL DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
