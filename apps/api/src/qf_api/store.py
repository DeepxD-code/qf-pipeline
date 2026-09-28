"""File store: storage/jobs/{id}.json. Rescanned on boot so redeploys keep history."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from qf_api.config import settings


def _root() -> Path:
    r = Path(settings.storage_dir)
    (r / "jobs").mkdir(parents=True, exist_ok=True)
    (r / "videos").mkdir(parents=True, exist_ok=True)
    (r / "cards").mkdir(parents=True, exist_ok=True)
    (r / "comps").mkdir(parents=True, exist_ok=True)
    return r


def new_job(topic: str) -> dict:
    now = datetime.now(UTC).isoformat()
    job = {
        "id": uuid.uuid4().hex[:12],
        "topic": topic,
        "topic_hash": topic_hash(topic),
        "status": "queued",
        "stage": "queued",
        "script": None,
        "video_url": None,
        "error": None,
        "created_at": now,
    }
    save(job)
    return job


def save(job: dict) -> None:
    (_root() / "jobs" / f"{job['id']}.json").write_text(json.dumps(job, indent=2))


def get(job_id: str) -> dict | None:
    p = _root() / "jobs" / f"{job_id}.json"
    return json.loads(p.read_text()) if p.exists() else None


def list_jobs(limit: int = 20) -> list[dict]:
    jobs = []
    for p in (_root() / "jobs").glob("*.json"):
        try:
            jobs.append(json.loads(p.read_text()))
        except Exception:
            continue
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return jobs[:limit]


def video_path(job_id: str) -> Path:
    return _root() / "videos" / f"{job_id}.mp4"


def topic_hash(topic: str) -> str:
    return hashlib.sha256(topic.strip().lower().encode()).hexdigest()[:16]


def find_ready_by_topic(topic: str) -> dict | None:
    """Idempotency cache: same normalized topic with a ready MP4 still on disk."""
    th = topic_hash(topic)
    for p in (_root() / "jobs").glob("*.json"):
        try:
            j = json.loads(p.read_text())
        except Exception:
            continue
        if j.get("topic_hash") == th and j.get("status") == "ready" and video_path(j["id"]).exists():
            return j
    return None


def comp_dir(job_id: str) -> Path:
    d = _root() / "comps" / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def cards_dir(job_id: str) -> Path:
    d = _root() / "cards" / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d
