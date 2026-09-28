# Qoneqt × CTRL FREAK — AI Content Pipeline

LLM-powered pipeline that turns a Topic / Prompt / Idea / Trend into a
ready-to-publish **Qoneqt Global Feed video (1080x1920, MP4)**.

> Mission from `challenge.pdf`: don't just use Qoneqt — build technology for Qoneqt.
> Judged on what is **built and shipped**: public GitHub + live deployment + demo video + 1 video published on Qoneqt.

## Why this wins on shipping

Every team can demo a pipeline. We ship like prod (RFQ-UPS pattern, slimmed for hack speed):

- **Single-service deploy** — one FastAPI service serves API + demo web + MP4 files. No Postgres/Redis required for v0. Deploys to Render/Railway/Fly in one click.
- **File-based jobs** — `storage/jobs/*.json` + `storage/videos/*.mp4`. Swappable to Postgres/Celery later (see `ARCHITECTURE.md` ADR-002).
- **Key-optional LLM** — works with zero API keys (deterministic template engine). Plug `OPENAI_API_KEY` / `GROQ_API_KEY` in to upgrade scripting with no code change.
- **Real ffmpeg compose** — Pillow cards (1080x1920) → ffmpeg H.264 MP4. Not a mock.
- **CI + Docker + tests** — `make check` runs lint + tests. Docker image builds and boots with `GET /health` green.

## Quick start (60s)

```bash
cp .env.example .env
pip install -e ".[dev]"
make run-api
# open http://localhost:8000/  -> paste a topic -> Generate -> preview MP4
```

Sample render without server:

```bash
make render-sample TOPIC="AI communities in Kochi"
# -> storage/videos/sample.mp4
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Demo web UI |
| GET | `/health`, `/ready`, `/live` | Probes |
| POST | `/api/v1/jobs` `{"topic": "..."}` | Enqueue pipeline, 202 + `job_id` |
| GET | `/api/v1/jobs/{id}` | Job status + script + `video_url` |
| GET | `/api/v1/jobs` | List jobs (latest first) |
| GET | `/v/{id}.mp4` | Serve rendered MP4 |

## Project structure

```
├── apps/api/            # FastAPI service (Python backend: API + worker + static web)
├── workers/
│   ├── java-renderer/   # Pure-JDK ffmpeg composer (virtual threads + Semaphore(2))
│   └── java-backend/    # Pure-JDK backend: same API + Java2D cards + java compose (make run-java-api)
├── apps/web/index.html  # Demo UI (served at / by either backend)
├── packages/
│   ├── qf_script/       # LLM -> hook/script/scene plan (key-optional)
│   ├── qf_visuals/      # Cinematic 1080x1920 cards (glow + floating UI + captions)
│   └── qf_compose/      # Ken Burns drift + xfade cuts -> MP4 (optional QF_MUSIC bed)
├── storage/             # jobs/*.json, videos/*.mp4 (gitignored except .gitkeep)
├── infra/               # (v0: root Dockerfile + docker-compose.yml)
├── scripts/render_sample.py
├── tests/
├── Makefile | pyproject.toml | Dockerfile | docker-compose.yml
├── ARCHITECTURE.md
└── challenge.pdf
```

## Publish to Qoneqt (manual step judges require)

1. Generate video in demo UI.
2. Download MP4 from `/v/{id}.mp4`.
3. Upload to Qoneqt Global Feed from your account.
4. Paste Qoneqt post URL into `docs/SHIP_LOG.md`.

## Env

See `.env.example`. Only real knob: `STORAGE_DIR` (default `storage`).
Optional upgrades: `OPENAI_API_KEY`, `GROQ_API_KEY`.
Scale knobs: `QF_VISUALS=cards|hyperframes`, `QF_COMPOSER=python|java`, `MAX_CONCURRENT_RENDERS=2`.

## Backends (same API, same storage schema)

| Backend | Run | Notes |
|---------|-----|-------|
| Python (default) | `make run-api` | FastAPI, Pillow cards, ffmpeg or Java composer |
| Java | `make run-java-api` | Pure JDK 21, zero deps, Java2D cards, bounded JVM composer |

Both read/write `storage/jobs/*.json` + `storage/videos/*.mp4`, so either serves
the other's renders. Java render speed equals Python's — ffmpeg does the encode
in native code either way; Java buys smaller footprint and faster cold start.
