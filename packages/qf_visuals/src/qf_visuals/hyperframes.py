"""qf_visuals hyperframes backend: cinema grammar, vertical 1080x1920.

Full-bleed photographic scenes, hard beat cuts, kinetic word-stagger
captions, drifting backgrounds, thin progress bar. No cards, no badges,
no panels — the reference grammar, not a dashboard.
"""

from __future__ import annotations

import html as _html
import shutil
import subprocess
from pathlib import Path


def total_duration(script, secs_per_image: float) -> float:
    return round(len(script.scenes) * secs_per_image, 2)


def _esc(s: object) -> str:
    t = _html.escape(str(s), quote=False)
    return t.replace("—", "-").replace("–", "-").replace("'", "'").replace(""", '"').replace(""", '"')


def build_composition(script, out_dir: str | Path, secs_per_image: float = 2.5) -> str:
    from qf_visuals.photo import fetch_photo

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    assets = out / "assets"
    assets.mkdir(exist_ok=True)
    total = total_duration(script, secs_per_image)
    scenes = list(script.scenes)
    clips: list[str] = []
    for i, s in enumerate(scenes):
        start = round(i * secs_per_image, 2)
        bg_tag = ""
        try:
            bg = fetch_photo(s.visual_prompt, assets / f"bg_{i + 1:02d}.jpg")
            bg_tag = f'<div class="bgwrap" id="qf-b{i}"><img class="bg" src="assets/{Path(bg).name}" /></div>'
        except Exception as exc:
            print(f"photo bg failed for scene {i + 1}, dark fallback: {exc}")
        words = str(s.caption).split() or ["Qoneqt"]
        nlines, cur, lines = 2, "", []
        for w in words:
            trial = f"{cur} {w}".strip()
            if len(trial) <= 12 or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        lines = lines[:nlines]
        flat = [w for line in lines for w in line.split()]
        spans, k = [], 0
        pos = 0
        for li, line in enumerate(lines):
            parts = []
            for w in line.split():
                hl = " hl" if li == len(lines) - 1 else ""
                parts.append(f'<span class="w{hl}" id="qf-c{i}-w{k}">{_esc(w)}</span>')
                k += 1
            pos += len(line.split())
            spans.append(f'<div class="cap-line">{" ".join(parts)}</div>')
        _ = flat, pos
        clips.append(f"""
    <div class="clip" data-start="{start}" data-duration="{secs_per_image}" data-track-index="{i}" id="qf-s{i}">
      {bg_tag}
      <div class="shade"></div>
      <div class="botgrad"></div>
      <div class="cap">{"".join(spans)}</div>
    </div>""")
    tweens: list[str] = []
    for i, s in enumerate(scenes):
        t0 = round(i * secs_per_image, 2)
        nw = len(str(s.caption).split())
        for k in range(nw):
            tweens.append(
                f'tl.fromTo("#qf-c{i}-w{k}", {{opacity:0, y:36}}, '
                f'{{opacity:1, y:0, duration:0.28, ease:"power3.out"}}, {round(t0 + 0.15 + k * 0.09, 2)});'
            )
        zin = i % 2 == 0
        tweens.append(
            f'tl.fromTo("#qf-b{i}", {{scale:{1.0 if zin else 1.12}}}, '
            f'{{scale:{1.12 if zin else 1.0}, duration:{secs_per_image}, ease:"none"}}, {t0});'
        )
    tweens.append(
        f'tl.fromTo("#qf-prog", {{scaleX:0}}, {{scaleX:1, duration:{total}, ease:"none"}}, 0);'
    )
    index = f"""<!doctype html>
<html><head><meta charset="utf-8" />
<style>
  html,body {{ margin:0; padding:0; background:#000; }}
  #root {{ width:100%; height:100%; position:relative; overflow:hidden; background:#000; }}
  .clip {{ position:absolute; inset:0; overflow:hidden; }}
  .bgwrap {{ position:absolute; inset:0; }}
  .bg {{ position:absolute; left:0; top:-46px; width:100%; height:calc(100% + 92px); object-fit:cover; }}
  .shade {{ position:absolute; inset:0; background:rgba(5,5,12,0.30); }}
  .botgrad {{ position:absolute; left:0; right:0; bottom:0; height:760px;
    background:linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0.72) 100%); }}
  .cap {{ position:absolute; left:80px; bottom:330px; width:920px; }}
  .cap-line {{ font-size:118px; font-weight:800; line-height:1.06; color:#fff;
    font-family:Arial,Helvetica,sans-serif; }}
  .cap-line .hl {{ color:#ffe878; }}
  .w {{ display:inline-block; }}
  .prog {{ position:absolute; top:0; left:0; height:10px; width:100%; background:rgba(255,255,255,0.22); }}
  .progfill {{ height:100%; width:100%; background:#ffe878; transform-origin:left center; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
</head><body>
<div data-composition-id="qf" data-width="1080" data-height="1920" data-duration="{total}" id="root">
  <div class="prog"><div class="progfill" id="qf-prog"></div></div>
{''.join(clips)}
</div>
<script>
  (function () {{
    var tl = gsap.timeline({{ paused: true }});
    {' '.join(tweens)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines["qf"] = tl;
  }})();
</script>
</body></html>
"""
    p = out / "index.html"
    p.write_text(index)
    return str(p)


def render_composition(comp_dir: str | Path, out_mp4: str | Path) -> str:
    import os as _os

    npx = shutil.which("npx")
    if not npx:
        raise RuntimeError("npx not found on PATH (need Node 22+ for hyperframes render)")
    out = Path(out_mp4)
    out.parent.mkdir(parents=True, exist_ok=True)
    comp_path = Path(comp_dir)
    if comp_path.is_file() or comp_path.suffix == ".html":
        comp_path = comp_path.parent

    def _rel(p: Path) -> str:
        try:
            return str(Path(_os.path.relpath(p)).as_posix())
        except Exception:
            return str(p.resolve()).replace("\\", "/")

    cmd = [npx, "hyperframes", "render", _rel(comp_path), "--output", _rel(out)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    if p.returncode != 0 or not out.exists():
        import contextlib as _cl

        with _cl.suppress(Exception):
            log = comp_path / "render-debug.log"
            log.write_text(f"CMD: {cmd}\nRC: {p.returncode}\n---STDOUT---\n{p.stdout}\n---STDERR---\n{p.stderr}")
        tail = ((p.stderr or "") + (p.stdout or ""))[-2000:]
        raise RuntimeError(f"hyperframes render failed (log in comp dir): {tail}")
    return str(out)
