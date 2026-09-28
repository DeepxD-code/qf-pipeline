"""QF API — single-service FastAPI: API + demo web + MP4 serving."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from qf_api import store
from qf_api.config import settings
from qf_api.pipeline import ffmpeg_available
from qf_api.routes import router

app = FastAPI(title="Qoneqt x CTRL FREAK — AI Content Pipeline", version="0.1.0")

# The showcase site is served from a different origin than this API (Vercel CDN
# vs container host), so the browser needs explicit CORS to call it at all.
# Credentials are not used: the API is unauthenticated, so a wildcard origin is
# safe here and avoids a deploy-time env var that is easy to forget.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

WEB_DIR = Path(__file__).resolve().parents[3] / "web"  # apps/api/src/qf_api -> apps/web
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


@app.get("/")
async def index():
    idx = WEB_DIR / "index.html"
    if idx.exists():
        return FileResponse(idx)
    return {"service": "qf-pipeline", "docs": "/docs"}


@app.get("/v/{job_id}.mp4")
async def serve_video(job_id: str):
    p = store.video_path(job_id)
    if not p.exists():
        return JSONResponse(status_code=404, content={"detail": "video not ready"})
    return FileResponse(p, media_type="video/mp4", filename=f"qoneqt-{job_id}.mp4")


@app.get("/health")
async def health():
    try:
        r = Path(settings.storage_dir)
        (r / "jobs").mkdir(parents=True, exist_ok=True)
        probe = r / "jobs" / ".writetest"
        probe.write_text("ok")
        probe.unlink(missing_ok=True)
        writable = True
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(exc)})
    ff = ffmpeg_available()
    code = 200 if (writable and ff) else 503
    return JSONResponse(
        status_code=code,
        content={
            "status": "healthy" if code == 200 else "unhealthy",
            "checks": {"storage": "ok", "ffmpeg": "ok" if ff else "missing"},
        },
    )


@app.get("/ready")
async def ready():
    return await health()


@app.get("/live")
async def live():
    return {"status": "healthy", "service": "qf-pipeline"}


@app.get("/metrics", include_in_schema=False)
async def metrics():
    n = len(store.list_jobs(limit=1000))
    return JSONResponse(content={"qf_jobs_total": n})
