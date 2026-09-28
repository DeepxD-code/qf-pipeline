# QF Architecture (v0 — ship-first, RFQ-UPS lineage)

## System overview

```
Topic/Prompt/Idea/Trend
  -> POST /api/v1/jobs
  -> qf_script (LLM w/ template fallback => hook + 3 scenes)
  -> qf_visuals (Pillow 1080x1920 cards)
  -> qf_compose (ffmpeg => H.264 MP4, 9:16)
  -> storage/videos/{id}.mp4 served at /v/{id}.mp4
  -> human uploads MP4 to Qoneqt Global Feed
```

Same monorepo discipline as RFQ-UPS (`apps/` deployables, `packages/` libs,
`Makefile`, `pyproject.toml`, CI, Docker, `ARCHITECTURE.md`) but slimmed for a
48h hack: **no Postgres/Redis/Chroma/Ollama in v0**.

## Components

### apps/api (`qf_api`)
FastAPI single service. Owns HTTP, job store (JSON files), background runner
(`asyncio.create_task`, no broker), static mount for `apps/web`, file serving
for `/v/*.mp4`. Health contract mirrors RFQ-UPS: `/health` checks storage
writability + ffmpeg presence; `/ready` same; `/live` always 200 when process
is up.

Endpoints: see README. Job state machine:
`queued -> scripting -> visuals -> composing -> ready | failed`.

### packages/qf_script
`generate_script(topic) -> Script`. Provider chain:
1. OpenAI (`OPENAI_API_KEY`, model `OPENAI_MODEL`, default `gpt-4o-mini`) if set.
2. Groq (`GROQ_API_KEY`, default `llama-3.3-70b-versatile`) if set.
3. Deterministic template (always works, zero keys, test-stable).

Output schema is Pydantic-validated in both paths so the pipeline never breaks
on LLM drift.

### packages/qf_visuals
Pillow cards, 1080x1920, gradient bg + topic + scene title + caption + scene
index. Pure function `render_cards(script, out_dir) -> [paths]`. No network,
no model download — renders offline in <1s.

Swap path (v1, not v0): replace card renderer with Pollinations/SD image URL
fetch; interface stays `[paths]`.

### packages/qf_compose
`compose_slideshow(images, out_mp4, secs_per_image=2.5, fps=30)` shells to
system `ffmpeg` (`-loop 1 -t -framerate -pix_fmt yuv420p -c:v libx264`).
Raises `RuntimeError` with stderr tail when ffmpeg is missing/fails so the job
lands in `failed` with a legible error instead of hanging.

## Data

No DB in v0. `STORAGE_DIR/`:
- `jobs/{id}.json` — full job incl. script + status + error
- `videos/{id}.mp4` — rendered output

Listed in-memory + rescanned from disk on boot so a redeploy keeps history.

## ADRs

- **ADR-001 single-service deploy.** One container serves everything. Rationale:
  judges open one URL; free-tier hosts give one service; multi-service compose
  (RFQ-UPS style) is documented in `docker-compose.yml` comments for later.
- **ADR-002 file store first, Postgres later.** Rationale: zero infra to break
  during demo; `store.py` is a 100-line seam — replace with SQLAlchemy without
  touching routes/pipeline.
- **ADR-003 asyncio tasks, not Celery, for v0.** Rationale: no broker to
  operate; concurrency need is ~3 parallel renders. Celery worker entrypoint
  shape is kept in `pipeline.py` (`run_job_sync`) so migration is mechanical.
- **ADR-004 template fallback is a feature.** Rationale: pipeline must demo on
  stage Wi-Fi with expired keys and still produce a valid MP4.

- **ADR-005 Java backend is a port, not a speedup.** Rationale: per-encode CPU
  is identical (ffmpeg, native code). The pure-JDK service (`workers/`) exists
  for smaller footprint, faster cold start, and bounded rendering
  (Semaphore(2) + virtual threads). Same HTTP contract and storage schema as
  the Python service, so either backend serves the other's jobs.
- **ADR-006 HyperFrames visuals are opt-in with fallback.** Rationale: motion
  compositions (per `skills/heygen-hyperframes/SKILL.md`) beat static cards,
  but a failed `npx hyperframes render` (no Chrome, no network for the GSAP
  CDN) must never fail the job — `QF_VISUALS=hyperframes` falls back to cards.

## Observability (v0 minimal, RFQ-UPS compatible later)
- Structured status per job (`stage`, `error`, `timings`).
- `/metrics` returns stub `qf_jobs_total` counter text (Prometheus-scrapable).
- Logs to stdout; correlation = `job_id`.

## What v1 would add (post-hack, only if it helps distribution)
1. Real TTS voiceover (Coqui/Edge-TTS) + mux audio.
2. Stock/AI visuals (Pexels/Pollinations) behind `QF_VISUALS=ai` flag.
3. Postgres + Celery + S3 when >100 jobs/day.
