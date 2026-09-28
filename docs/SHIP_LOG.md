# Ship log

Judging requires one video published on the Qoneqt Global Feed. Paste the post
URL below once uploaded.

## Done

| Deliverable | Status | Evidence |
|---|---|---|
| Public GitHub repo | done | `github.com/DeepxD-code/qf-pipeline` |
| Topic → MP4 pipeline | done | 9/9 tests, `make render-sample TOPIC=...` |
| 1080×1920 h264+aac output | done | verified with `ffprobe` on every render |
| Copy/replica grammar, topic-driven | done | 6 beats, captions + backdrops from the script |
| Three art-style variations | done | noir / ember / mono, chosen per topic by hash |
| Edge-TTS narration + music + SFX | done | 7 SFX cut points per 22 s render |
| Python + Java backends | done | same API, same storage schema |
| Static showcase site | built | `apps/web`, `vercel.json`, `.vercelignore` |
| CORS for split-origin deploy | done | proven by `OPTIONS` preflight → 200 |
| Docker image | done | `docker build -t qf-pipeline .` |

## Needs a human (blocked on account access)

- [ ] **Vercel deploy** — run `vercel login`, then `npx vercel --prod`.
      Anonymous deploys are rejected by Vercel, so this cannot be automated.
      The build is verified: Vercel's own compiler emits valid output and the
      upload payload is 2.7 MB.
- [ ] **Container deploy** — push the image to Render / Railway / Fly and set
      `STORAGE_DIR` to the mounted volume. See `docs/DEPLOY.md`.
- [ ] **Video 1 on Qoneqt**: `<paste post url here>` (job id: `0d89cd00909f`,
      topic: "Monsoon tea stalls in Fort Kochi", 1080×1920, 4.23 MB)
- [ ] **Teammate admin** — `Dharmik-25` needs the pending invite accepted, then
      the role dropdown on the repo's Manage access page set to Admin. GitHub's
      API caps collaborator grants at `write` for this account (REST returns
      `Cannot assign ... permission of admin`, and GraphQL exposes no mutation
      for it), so the UI is the only route.

## Candidate videos to publish

| File | Topic | Specs |
|---|---|---|
| `storage/videos/0d89cd00909f.mp4` | Monsoon tea stalls in Fort Kochi | 1080×1920, 4.23 MB (cards backend, 7.5 s) |
| `storage/videos/show-chai.mp4` | Chai tapri sunrise regulars | 1080×1920, 22 s, ember |
| `storage/videos/show-keyboard.mp4` | Mechanical keyboard build | 1080×1920, 22 s, mono |
| `storage/videos/show-maggi.mp4` | Maggi instant noodles review | 1080×1920, 22 s, noir |

The `show-*.mp4` files are the strongest submission: 22 s, full 6-beat grammar,
narration plus music plus SFX, and visibly different per topic.
