import os

os.environ.setdefault("STORAGE_DIR", "storage")


def test_template_script_has_3_scenes():
    from qf_script import template_script

    s = template_script("AI communities in Kochi")
    assert len(s.scenes) == 3
    assert s.hook
    assert all(x.caption and x.voiceover for x in s.scenes)


def test_generate_script_never_needs_keys():
    from qf_script import generate_script

    for k in ("OPENAI_API_KEY", "GROQ_API_KEY"):
        os.environ.pop(k, None)
    s = generate_script("Campus creators")
    assert len(s.scenes) == 3


def test_cards_and_compose(tmp_path):
    import shutil

    from qf_compose import compose_slideshow
    from qf_script import template_script
    from qf_visuals import render_cards

    if shutil.which("ffmpeg") is None:
        import pytest

        pytest.skip("ffmpeg not on PATH")
    s = template_script("Test topic")
    imgs = render_cards(s, tmp_path / "cards")
    assert len(imgs) == 3
    out = tmp_path / "out.mp4"
    compose_slideshow(imgs, out, secs_per_image=1.0)
    assert out.exists() and out.stat().st_size > 10_000


def test_api_contract():
    from fastapi.testclient import TestClient
    from qf_api.main import app

    c = TestClient(app)
    assert c.get("/live").status_code == 200
    r = c.post("/api/v1/jobs", json={"topic": "API contract topic"})
    assert r.status_code == 202
    jid = r.json()["job_id"]
    assert c.get(f"/api/v1/jobs/{jid}").status_code == 200
    assert c.get("/api/v1/stats").status_code == 200


def test_hyperframes_composition_builds(tmp_path):
    from qf_visuals.hyperframes import build_composition

    from qf_script import template_script

    s = template_script("Hyperframes test")
    idx = build_composition(s, tmp_path / "comp", secs_per_image=2.0)
    text = (tmp_path / "comp" / "index.html").read_text()
    assert idx.endswith("index.html")
    assert 'data-composition-id="qf"' in text
    assert text.count('class="clip"') == 3
    assert 'window.__timelines["qf"]' in text


def test_topic_cache_reuses_ready(tmp_path, monkeypatch):
    import qf_api.store as store

    monkeypatch.setattr(store.settings, "storage_dir", str(tmp_path))
    job = store.new_job("Same Topic Cache")
    job["status"] = "ready"
    store.save(job)
    store.video_path(job["id"]).write_bytes(b"\x00" * 16)
    hit = store.find_ready_by_topic("same topic cache")
    assert hit and hit["id"] == job["id"]


def test_java_composer(tmp_path):
    import shutil

    from qf_compose import compose_slideshow
    from qf_script import template_script
    from qf_visuals import render_cards

    if shutil.which("ffmpeg") is None or shutil.which("java") is None:
        import pytest

        pytest.skip("ffmpeg+java needed")
    from qf_compose import compose_java

    classes = __import__("pathlib").Path(__file__).resolve().parents[1] / "workers" / "java-renderer" / "classes"
    if not (classes / "Compose.class").exists():
        import pytest

        pytest.skip("java renderer not built (run workers/java-renderer/build.bat)")
    s = template_script("Java compose test")
    imgs = render_cards(s, tmp_path / "cards")
    out = tmp_path / "java.mp4"
    compose_java(imgs, out, secs_per_image=1.0)
    assert out.exists() and out.stat().st_size > 10_000
    out2 = tmp_path / "py.mp4"
    compose_slideshow(imgs, out2, secs_per_image=1.0)
    assert out2.exists()


def test_photo_backend(tmp_path):
    import pytest
    from qf_visuals.photo import render_photo_cards

    from qf_script import template_script

    try:
        s = template_script("Photo backend test")
        imgs = render_photo_cards(s, tmp_path / "photo")
    except Exception as exc:
        pytest.skip(f"photo backend needs network: {exc}")
    assert len(imgs) == 3
    assert all(__import__("pathlib").Path(p).stat().st_size > 10_000 for p in imgs)


def test_voiceover(tmp_path):
    import pytest

    from qf_script import template_script
    from qf_voice import build_voiceover

    try:
        s = template_script("Voiceover test")
        mp3 = build_voiceover(s, tmp_path / "vo", 2.5)
    except Exception as exc:
        pytest.skip(f"voiceover needs network: {exc}")
    if mp3 is None:
        pytest.skip("voiceover returned None (TTS unavailable)")
    assert __import__("pathlib").Path(mp3).stat().st_size > 1000
