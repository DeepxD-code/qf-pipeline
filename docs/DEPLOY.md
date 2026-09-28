# Deploying QF Pipeline

Two halves, two hosts. They cannot be the same host — see the table below.

## 1. Renderer API (required for the live "generate" button)

Needs **ffmpeg**, a **writable volume**, and **~70 s per render**. That rules out
serverless functions (Vercel/Netlify have no ffmpeg binary, a read-only FS, and
function timeouts well under a render). Deploy as a container to Render,
Railway, or Fly.

```bash
docker build -t qf-pipeline .
docker run -p 8000:8000 -v qf-storage:/app/storage qf-pipeline
```

On a container host, set:

| Var | Value | Why |
|---|---|---|
| `PORT` | platform-assigned | the Dockerfile honours it |
| `STORAGE_DIR` | `/app/storage` | must point at the mounted volume |
| `MAX_CONCURRENT_RENDERS` | `2` (default) | bounds ffmpeg CPU/RAM |
| `QF_VISUALS` | `copy` for 22 s output | `cards` (default) gives ~7.5 s |

Then confirm the renderer is healthy before pointing a browser at it:

```bash
curl -fsS https://your-api.example.com/health
# {"status":"healthy","checks":{"storage":"ok","ffmpeg":"ok"}}
```

A 503 means the volume is not writable or ffmpeg is missing — both are fixable
at the host, and the `/health` body names which one failed.

## 2. Showcase site (Vercel, static)

`apps/web/` is dependency-free static HTML/CSS. `vercel.json` sets
`outputDirectory: apps/web` with no build step; `.vercelignore` keeps the Python
tree and the 100 MB+ of render output out of the upload (the deploy payload is
~2.7 MB).

```bash
npm install -g vercel
vercel login                 # REQUIRED - anonymous deploys are rejected
npx vercel --prod
```

## 3. Point the site at the API

The site and API are on different domains, so the page takes the API base as a
query param:

```
https://your-site.vercel.app/?api=https://your-api.example.com
```

On load the page calls `<api>/health` and picks one of two states:

- **200** → button becomes "Generate video", live rendering enabled
- **anything else** → button becomes "Renderer offline" and is disabled, with
  deploy instructions shown

So a judge never clicks a button that cannot work. CORS is already handled
server-side (`allow_origins=["*"]`, no credentials — the API is unauthenticated).

## Local equivalent

```bash
python -m uvicorn qf_api.main:app --port 8000
# http://localhost:8000/  - same page, same origin, no ?api= needed
```
