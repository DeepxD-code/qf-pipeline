"""Pipeline runner. Sync core (run_job_sync) so a future Celery worker can reuse it.

Scalability notes (hack-grade, honest):
- ffmpeg does the encode in native code either way; Python-vs-Java per-encode
  CPU is a wash. The wins are: bounded concurrency (Semaphore), idempotency
  cache (same topic reuses MP4), and a low-memory Java composer option.
- QF_VISUALS=cards (default, offline Pillow) | hyperframes (motion HTML render,
  falls back to cards on any failure so the demo never breaks) | photo
  (AI-photographic backgrounds via Pollinations FLUX, free/no-key, falls back).
- QF_COMPOSER=python (default) | java (workers/java-renderer, Semaphore(2)).
- QF_VOICE=1 (default) free Edge-TTS narration, silent fallback.
"""

from __future__ import annotations

import asyncio
import shutil
import traceback

from qf_api import store
from qf_api.config import settings

_render_sem: asyncio.Semaphore | None = None


def _sem() -> asyncio.Semaphore:
    global _render_sem
    if _render_sem is None:
        _render_sem = asyncio.Semaphore(max(1, int(settings.max_concurrent_renders)))
    return _render_sem


def full_audio(script, job_id: str, spi: float, video_path: str, total_dur: float, scene_step: float) -> None:
    """Voice + brag music bed + SFX hits muxed under video_path in place. Never raises."""
    try:
        from qf_audio import MUSIC, build_sfx_track, mix_final, scene_sfx_events
        from qf_voice import build_voiceover

        voice = (
            build_voiceover(script, store.cards_dir(job_id), spi)
            if settings.qf_voice.strip() == "1"
            else None
        )
        sfx = build_sfx_track(
            scene_sfx_events(len(script.scenes), scene_step), total_dur, store.cards_dir(job_id) / "sfx.mp3"
        )
        tmp = str(video_path) + ".mix.mp4"
        mix_final(video_path, voice, str(MUSIC) if MUSIC.exists() else None, sfx, total_dur, tmp)
        shutil.move(tmp, video_path)
    except Exception as exc:
        print(f"audio mix failed, continuing: {exc}")


def run_job_sync(job_id: str, secs_per_image: float | None = None) -> None:
    from qf_visuals.hyperframes import build_composition, render_composition
    from qf_visuals.photo import render_photo_cards

    from qf_compose import compose_java, compose_slideshow
    from qf_script import generate_script
    from qf_visuals import render_cards

    job = store.get(job_id)
    if not job:
        return
    spi = secs_per_image or float(settings.secs_per_image)
    try:
        # Idempotency: reuse a ready MP4 for the same normalized topic.
        hit = store.find_ready_by_topic(job["topic"])
        if hit and hit["id"] != job_id:
            job["status"] = "ready"
            job["stage"] = "ready"
            job["script"] = hit.get("script")
            store.save(job)
            shutil.copyfile(store.video_path(hit["id"]), store.video_path(job_id))
            job["video_url"] = f"/v/{job_id}.mp4"
            store.save(job)
            return

        job["status"] = "running"
        job["stage"] = "scripting"
        store.save(job)
        script = generate_script(job["topic"])
        for s in script.scenes:
            s.duration_s = spi
        job["script"] = script.model_dump()
        job["stage"] = "visuals"
        store.save(job)

        # Visual backend routing (per skills/heygen-hyperframes/SKILL.md).
        backend = settings.qf_visuals.strip().lower()
        hf_mp4: str | None = None
        if backend == "copy":
            # Exact-grammar replica: persistent world, blur-crossfade melts, music-only.
            try:
                from qf_visuals.copy import build_copy

                from qf_audio import MUSIC, build_sfx_track, mix_final

                comp = build_copy(script, store.comp_dir(job_id))
                job["script"] = {"topic": job["topic"], "mode": "copy", "beats": 6}
                job["stage"] = "composing"
                store.save(job)
                tmp = str(store.video_path(job_id)) + ".raw.mp4"
                render_composition(comp, tmp)
                cuts = [3.1, 6.6, 10.1, 13.6, 17.1]
                ev = [(0.15, "impact/impactBell_heavy_000.ogg", 0.5)]
                cuts_sfx = ["interface/switch_004.ogg", "interface/switch_006.ogg", "interface/drop_003.ogg"]
                for k, cut in enumerate(cuts):
                    ev.append((cut, cuts_sfx[k % len(cuts_sfx)], 0.7))
                ev += [(17.3, "impact/impactBell_heavy_000.ogg", 0.8),
                       (21.0, "impact/impactSoft_medium_000.ogg", 0.7)]
                sfx = build_sfx_track(ev, 22.0, store.cards_dir(job_id) / "sfx.mp3")
                mix_final(tmp, None, str(MUSIC) if MUSIC.exists() else None, sfx,
                          22.0, str(store.video_path(job_id)), music_vol=0.4)
                hf_mp4 = str(store.video_path(job_id))
            except Exception as exc:
                print(f"copy backend failed, falling back to cards: {exc}")
                hf_mp4 = None
        if hf_mp4 is None:
            try:
                comp = build_composition(script, store.comp_dir(job_id), secs_per_image=spi)
                hf_mp4 = render_composition(comp, store.video_path(job_id))
                full_audio(script, job_id, spi, hf_mp4, round(len(script.scenes) * spi, 3), spi)
            except Exception as exc:
                print(f"hyperframes backend failed, falling back to cards: {exc}")
                hf_mp4 = None
        if hf_mp4 is None:
            if backend == "photo":
                try:
                    cards = render_photo_cards(script, store.cards_dir(job_id))
                except Exception as exc:
                    print(f"photo backend failed, falling back to cards: {exc}")
                    cards = render_cards(script, store.cards_dir(job_id))
            else:
                cards = render_cards(script, store.cards_dir(job_id))
            job["stage"] = "composing"
            store.save(job)
            if settings.qf_composer.strip().lower() == "java":
                try:
                    compose_java(cards, store.video_path(job_id), secs_per_image=spi)
                except Exception as exc:
                    print(f"java composer failed, falling back to python: {exc}")
                    compose_slideshow(cards, store.video_path(job_id), secs_per_image=spi)
            else:
                compose_slideshow(cards, store.video_path(job_id), secs_per_image=spi)
            total = round(len(script.scenes) * spi - 0.5 * (len(script.scenes) - 1), 3)
            full_audio(script, job_id, spi, str(store.video_path(job_id)), total, round(spi - 0.5, 3))

        job["status"] = "ready"
        job["stage"] = "ready"
        job["video_url"] = f"/v/{job_id}.mp4"
        store.save(job)
    except Exception as exc:
        job["status"] = "failed"
        job["stage"] = "failed"
        job["error"] = f"{exc}"
        store.save(job)
        traceback.print_exc()


async def run_job_async(job_id: str, secs_per_image: float | None = None) -> None:
    async with _sem():
        await asyncio.to_thread(run_job_sync, job_id, secs_per_image)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None
