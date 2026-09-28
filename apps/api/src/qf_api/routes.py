from fastapi import APIRouter, BackgroundTasks, HTTPException

from qf_api import store
from qf_api.pipeline import run_job_async
from qf_api.schemas import JobCreate

router = APIRouter()


@router.post("/jobs", status_code=202)
async def create_job(body: JobCreate, bg: BackgroundTasks):
    topic = body.topic.strip()
    hit = store.find_ready_by_topic(topic)
    if hit:
        return {"job_id": hit["id"], "status": "ready", "cached": True}
    job = store.new_job(topic)
    bg.add_task(run_job_async, job["id"], body.secs_per_image)
    return {"job_id": job["id"], "status": job["status"], "cached": False}


@router.get("/jobs")
async def list_jobs():
    return {"jobs": store.list_jobs()}


@router.get("/stats")
async def stats():
    from qf_api.config import settings as _s

    jobs = store.list_jobs(limit=1000)
    by_status: dict[str, int] = {}
    for j in jobs:
        by_status[j.get("status", "?")] = by_status.get(j.get("status", "?"), 0) + 1
    return {
        "total": len(jobs),
        "by_status": by_status,
        "backend": {"visuals": _s.qf_visuals, "composer": _s.qf_composer},
        "max_concurrent_renders": _s.max_concurrent_renders,
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job
