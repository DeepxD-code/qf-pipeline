"""qf_visuals copy builder: exact-grammar replica of the reference promo.

Reference anatomy (23.5s status video, 6 beats x ~3.5s):
Reference grammar adapted per-topic (was: persistent orb world):
- Backdrops drawn from each scene's visual prompt (paired for continuity)
- Captions from the script: hook punch, voiceover fragments, trio, title
- Floating app windows fly in/out above it (once fanned 3-up in perspective)
- Phone-notch pill morphs at top; captions white-bold + blue accent, centered
- Title cards ("Smart Notch" + dim subline); MUSIC ONLY, no voiceover

Copy maps our product onto every beat. Music-only + cut SFX (no voice).
"""

from __future__ import annotations

import html as _html
from pathlib import Path

CAP = "Qoneqt Pipeline"
SUB = "Topic in. MP4 out."

STYLES = {
    # noir: midnight orb, blue punch, lower-third captions (the reference look)
    "noir": {
        "bg": "dark blue night, glowing horizon",
        "accent": "#8ab8ff",
        "cap_css": "left:0; right:0; bottom:330px; text-align:center;",
        "shade": 0.30,
        "vignette": True,
        "music": "happy-beats-business-moves-vol-1-by-ende-dot-app.mp3",
    },
    # ember: warm concert fire, orange punch, centered captions
    "ember": {
        "bg": "golden ember concert fire glow, warm stage",
        "accent": "#ffb14e",
        "cap_css": "left:0; right:0; bottom:850px; text-align:center;",
        "shade": 0.34,
        "vignette": True,
        "music": "happy-beats-business-moves-vol-11-by-ende-dot-app.mp3",
    },
    # mono: desaturated urban night, all-white punch, top-third captions
    "mono": {
        "bg": "desaturated urban night street, moody monochrome",
        "accent": "#ffffff",
        "cap_css": "left:0; right:0; top:300px; text-align:center;",
        "shade": 0.42,
        "vignette": False,
        "music": "happy-beats-business-moves-vol-12-by-ende-dot-app.mp3",
    },
}


def choose_style(topic: str, explicit: str = "auto") -> str:
    explicit = (explicit or "auto").strip().lower()
    if explicit in STYLES:
        return explicit
    import hashlib

    h = int(hashlib.sha256(topic.strip().lower().encode()).hexdigest(), 16)
    return list(STYLES)[h % len(STYLES)]


def style_music(style: str) -> Path:
    from qf_audio import mix as _mix

    default = _mix.MUSIC
    name = STYLES.get(style, STYLES["noir"])["music"]
    p = default.parent / name
    return p if p.exists() else default


def _esc(s: object) -> str:
    return _html.escape(str(s), quote=False)


def _frag(text: str, n: int = 5) -> str:
    words = str(text).split()
    return " ".join(words[:n]).upper() or "QONEQT"


def build_copy(script, out_dir: str | Path, style: str = "auto") -> str:
    """Topic-drawn beats in a resolved art style (same fluidity, different look)."""
    """6 beats from a 3-scene script: every caption, window and backdrop is topic-drawn.

    Backdrops pair up (beats 1-2, 3-4, 5-6 share) for continuity with variety.
    """
    from qf_visuals.photo import fetch_photo

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    assets = out / "assets"
    assets.mkdir(exist_ok=True)
    topic = script.topic
    st = STYLES[choose_style(topic, style)]
    accent = st["accent"]
    shade = st["shade"]
    cap_css = st["cap_css"]
    vig_tag = '<div class="vig"></div>' if st["vignette"] else ""
    scenes = list(script.scenes)
    bg_files: list[str] = []
    roles = [
        "dramatic hero shot, cinematic still",
        "real life scene with people, photorealistic",
        "climax moment, golden hour energy",
    ]
    for i, _s in enumerate(scenes):
        try:
            prompt = f"{topic.strip()}, {roles[i % len(roles)]}, {st['bg']}, vertical photo, no text"
            bg = fetch_photo(prompt, assets / f"bg_{i + 1:02d}.jpg")
            bg_files.append(f"assets/{Path(bg).name}")
        except Exception as exc:
            print(f"photo bg failed for scene {i + 1}, black fallback: {exc}")
            bg_files.append("")
    while len(bg_files) < 3:
        bg_files.append("")
    bgmap = [bg_files[0], bg_files[0], bg_files[1], bg_files[1], bg_files[2], bg_files[2]]
    t = (topic.strip() or "Qoneqt").split()
    tshort = " ".join(t[:3])
    punch = _frag(topic, 4)
    v1, v2 = _frag(scenes[0].voiceover), _frag(scenes[1].voiceover)
    w1 = scenes[0].voiceover.split()
    lyr1, lyr2 = " ".join(w1[:6]), " ".join(w1[6:12])
    beats = [
        # (start, dur, caption_html, pill, window_kind)
        (0.0, 3.5, 'STOP <span class="bld">SCROLLING</span>', "Topic in -> MP4 out", "topic"),
        (3.1, 3.5, _html.escape(punch), "Scripting...", "script"),
        (6.6, 3.5, _html.escape(v1), "Narrating...", "player"),
        (10.1, 3.5, _html.escape(v2), "Rendering...", "bars"),
        (13.6, 3.5, 'Script. Visuals. <span class="bld">Video.</span>', "Composing...", "trio"),
        (17.1, 4.9, "", "", "title"),
    ]
    clips: list[str] = []
    for bi, (start, dur, cap, pill, kind) in enumerate(beats):
        win = ""
        if kind == "topic":
            win = f"""
        <div class="win" id="qf-w{bi}">
          <div class="chrome"><span class="d"></span><span class="d"></span><span class="d"></span></div>
          <div class="tin">New video</div>
          <div class="tline">{_esc(tshort)}</div>
          <div class="go" id="qf-go{bi}">Generate</div>
        </div>"""
        elif kind == "script":
            win = f"""
        <div class="win" id="qf-w{bi}">
          <div class="chrome"><span class="d"></span><span class="d"></span><span class="d"></span></div>
          <div class="code" id="qf-l{bi}a">hook: "{_esc(tshort)}..."</div>
          <div class="code" id="qf-l{bi}b">scenes: 3 &times; vertical</div>
          <div class="code" id="qf-l{bi}c">voice: en-US</div>
        </div>"""
        elif kind == "player":
            win = f"""
        <div class="win" id="qf-w{bi}">
          <div class="chrome"><span class="d"></span><span class="d"></span><span class="d"></span></div>
          <div class="song">{_esc(tshort)}</div>
          <div class="lyr" id="qf-l{bi}a">{_esc(lyr1)}...</div>
          <div class="lyr hl2" id="qf-l{bi}b">{_esc(lyr2)}...</div>
          <div class="track"><div class="fill" id="qf-f{bi}"></div></div>
        </div>"""
        elif kind == "bars":
            win = f"""
        <div class="win" id="qf-w{bi}">
          <div class="chrome"><span class="d"></span><span class="d"></span><span class="d"></span></div>
          <div class="bar-label">SCRIPT</div>
          <div class="track"><div class="fill green" id="qf-f{bi}a"></div></div>
          <div class="bar-label">RENDER</div>
          <div class="track"><div class="fill green" id="qf-f{bi}b"></div></div>
          <div class="ready" id="qf-r{bi}">READY</div>
        </div>"""
        elif kind == "trio":
            win = f"""
        <div class="trio">
          <div class="mini" id="qf-m{bi}a"><div class="mt">SCRIPT</div></div>
          <div class="mini" id="qf-m{bi}b"><div class="mt">VISUALS</div></div>
          <div class="mini" id="qf-m{bi}c"><div class="mt">VIDEO</div></div>
        </div>"""
        elif kind == "title":
            win = f"""
        <div class="titlecard" id="qf-w{bi}">
          <div class="tt">{CAP}</div>
          <div class="ts">{SUB}</div>
        </div>"""
        pill_tag = f'<div class="pill" id="qf-p{bi}"><span class="dot"></span>{pill}</div>' if pill else ""
        cap_tag = f'<div class="cap" id="qf-c{bi}">{cap}</div>' if cap else ""
        bgm = bgmap[bi]
        bgshot = f'<img class="bg" src="{bgm}" />' if bgm else ""
        clips.append(f"""
    <div class="clip" data-start="{start}" data-duration="{dur}" data-track-index="{bi}" id="qf-s{bi}">
      {bgshot}
      <div class="xwrap" id="qf-x{bi}">
      {pill_tag}
      {win}
      {cap_tag}
      </div>
    </div>""")
    tw: list[str] = []
    for bi, (start, dur, _cap, _pill, kind) in enumerate(beats):
        if kind in ("topic", "script", "player", "bars"):
            tw.append(
                f'tl.fromTo("#qf-w{bi}", {{opacity:0, y:90}}, '
                f'{{opacity:1, y:0, duration:0.6, ease:"power3.out"}}, {start + 0.2});'
            )
            reps = max(1, int(dur / 1.6))
            tw.append(
                f'tl.to("#qf-w{bi}", {{y:-18, duration:0.8, ease:"sine.inOut", yoyo:true, repeat:{reps}}}, '
                f"{round(start + 0.8, 2)});"
            )
        elif kind == "trio":
            for k, m in enumerate("abc"):
                tw.append(
                    f'tl.fromTo("#qf-m{bi}{m}", {{opacity:0, y:80, rotation:{-8 + k * 8}}}, '
                    f'{{opacity:1, y:0, rotation:{-8 + k * 8}, duration:0.5, ease:"power3.out"}}, '
                    f"{round(start + 0.2 + k * 0.25, 2)});"
                )
        elif kind == "title":
            tw.append(
                f'tl.fromTo("#qf-w{bi} .tt", {{opacity:0, y:50}}, '
                f'{{opacity:1, y:0, duration:0.7, ease:"power3.out"}}, {start + 0.3});'
            )
            tw.append(
                f'tl.fromTo("#qf-w{bi} .ts", {{opacity:0}}, {{opacity:1, duration:0.6}}, {start + 1.0});'
            )
        if kind != "title":
            tw.append(
                f'tl.fromTo("#qf-c{bi}", {{opacity:0, y:34, filter:"blur(10px)"}}, '
                f'{{opacity:1, y:0, filter:"blur(0px)", duration:0.45, ease:"power3.out"}}, '
                f"{round(start + 0.55, 2)});"
            )
        if kind == "player":
            tw.append(
                f'tl.fromTo("#qf-f{bi}", {{width:"4%"}}, {{width:"88%", duration:{round(dur - 0.9, 2)}, '
                f'ease:"none"}}, {round(start + 0.7, 2)});'
            )
            for k, ln in enumerate("ab"):
                tw.append(
                    f'tl.fromTo("#qf-l{bi}{ln}", {{opacity:0}}, {{opacity:1, duration:0.4}}, '
                    f"{round(start + 0.9 + k * 0.7, 2)});"
                )
        if kind == "script":
            for k, ln in enumerate("abc"):
                tw.append(
                    f'tl.fromTo("#qf-l{bi}{ln}", {{opacity:0, x:-24}}, '
                    f'{{opacity:1, x:0, duration:0.35}}, {round(start + 0.7 + k * 0.4, 2)});'
                )
        if kind == "bars":
            tw.append(
                f'tl.fromTo("#qf-f{bi}a", {{width:"4%"}}, {{width:"96%", duration:1.0, ease:"power2.out"}}, '
                f"{round(start + 0.6, 2)});"
            )
            tw.append(
                f'tl.fromTo("#qf-f{bi}b", {{width:"4%"}}, {{width:"96%", duration:1.0, ease:"power2.out"}}, '
                f"{round(start + 1.2, 2)});"
            )
            tw.append(
                f'tl.fromTo("#qf-r{bi}", {{opacity:0, scale:0.8}}, '
                f'{{opacity:1, scale:1, duration:0.4}}, {round(start + 2.3, 2)});'
            )
        if kind == "topic":
            tw.append(
                f'tl.fromTo("#qf-go{bi}", {{scale:0.9}}, {{scale:1, duration:0.4, ease:"back.out(2)"}}, '
                f"{round(start + 1.4, 2)});"
            )
    # Blur-crossfade melts: outgoing content dissolves as the next beat resolves in.
    # No exit on the final beat (rule: transition IS the exit, last scene exempt).
    for bi in range(len(beats) - 1):
        cut = beats[bi + 1][0]
        tw.append(
            f'tl.to("#qf-x{bi}", {{opacity:0, filter:"blur(14px)", duration:0.5, ease:"power2.in"}}, {cut});'
        )
    total = 22.0
    index = f"""<!doctype html>
<html><head><meta charset="utf-8" />
<style>
  html,body {{ margin:0; padding:0; background:#000; }}
  #root {{ width:100%; height:100%; position:relative; overflow:hidden; background:#000; }}
  .world {{ position:absolute; inset:0; }}
  .shade {{ position:absolute; inset:0; background:rgba(4,4,10,{shade}); }}
  .vig {{ position:absolute; inset:0;
    background:radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%); }}
  .world img {{ position:absolute; left:0; top:-46px; width:100%; height:calc(100% + 92px); object-fit:cover; }}
  .clip .bg {{ position:absolute; left:0; top:-46px; width:100%; height:calc(100% + 92px); object-fit:cover; }}
  .clip {{ position:absolute; inset:0; overflow:hidden; }}
  .xwrap {{ position:absolute; inset:0; }}
  .pill {{ position:absolute; top:120px; left:50%; width:560px; margin-left:-280px; background:#0a0a10;
    border:2px solid #2a2a3a; border-radius:999px; padding:20px 0; text-align:center;
    font-size:32px; color:#e8e8f0; font-family:Arial,Helvetica,sans-serif; }}
  .pill .dot {{ display:inline-block; width:18px; height:18px; border-radius:50%; background:#4ae08a;
    margin-right:16px; }}
  .win {{ position:absolute; left:190px; top:560px; width:700px; background:#101018;
    border:3px solid #2a2a3a; border-radius:30px; padding:40px 46px;
    font-family:Arial,Helvetica,sans-serif; box-shadow:0 30px 80px rgba(0,0,0,0.6); }}
  .chrome {{ margin-bottom:22px; }}
  .chrome .d {{ display:inline-block; width:20px; height:20px; border-radius:50%; background:#3a3a4a;
    margin-right:12px; }}
  .tin {{ font-size:30px; color:#8a8a95; }}
  .tline {{ font-size:52px; font-weight:800; color:#fff; margin:10px 0 26px 0; }}
  .go {{ display:inline-block; background:#fff; color:#000; font-weight:800; font-size:36px;
    border-radius:16px; padding:18px 44px; }}
  .code {{ font-size:34px; color:#c8c8d6; margin-top:16px; }}
  .song {{ font-size:44px; font-weight:800; color:#fff; }}
  .lyr {{ font-size:36px; color:#c8c8d6; margin-top:14px; }}
  .lyr.hl2 {{ color:{accent}; }}
  .track {{ height:20px; background:#2a2a3a; border-radius:10px; margin-top:28px; overflow:hidden; }}
  .fill {{ height:100%; width:4%; background:{accent}; border-radius:10px; }}
  .fill.green {{ background:#4ae08a; }}
  .bar-label {{ font-size:30px; color:#c8c8d6; margin-top:26px; }}
  .ready {{ display:inline-block; margin-top:28px; background:#4ae08a; color:#06130b; font-weight:800;
    font-size:32px; border-radius:999px; padding:12px 34px; }}
  .trio {{ position:absolute; left:0; right:0; top:600px; display:flex; justify-content:center; gap:30px; }}
  .mini {{ width:280px; background:#101018; border:3px solid #2a2a3a; border-radius:26px; padding:44px 0;
    text-align:center; box-shadow:0 30px 80px rgba(0,0,0,0.6); }}
  .mini .mt {{ font-size:34px; font-weight:800; color:#fff; font-family:Arial,Helvetica,sans-serif; }}
  .titlecard {{ position:absolute; left:0; right:0; top:760px; text-align:center; }}
  .titlecard .tt {{ font-size:110px; font-weight:800; color:#fff; font-family:Arial,Helvetica,sans-serif; }}
  .titlecard .ts {{ font-size:40px; color:#e8e8f0; margin-top:18px; font-family:Arial,Helvetica,sans-serif;
    text-shadow:0 4px 30px rgba(0,0,0,0.95); }}
  .cap {{ position:absolute; left:0; right:0; {cap_css}; text-align:center; font-size:64px; font-weight:800;
    color:#fff; font-family:Arial,Helvetica,sans-serif; text-shadow:0 4px 34px rgba(0,0,0,0.95); }}
  .cap .bld {{ color:#8ab8ff; }}
  .cap .dim {{ color:#8a8a95; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
</head><body>
<div data-composition-id="qf" data-width="1080" data-height="1920" data-duration="{total}" id="root">
  <div class="world"><div class="shade"></div>{vig_tag}</div>
{''.join(clips)}
</div>
<script>
  (function () {{
    var tl = gsap.timeline({{ paused: true }});
    {' '.join(tw)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines["qf"] = tl;
  }})();
</script>
</body></html>
"""
    p = out / "index.html"
    p.write_text(index)
    return str(p)
