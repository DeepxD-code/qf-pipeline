# Hyperframes Composition Brief: QF Pipeline

## Objective
Create a short launch-style brag video for QF Pipeline (Qoneqt × CTRL FREAK AI content pipeline).

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 20 seconds

## Source Material
- Project root: `E:\Potential-gold\CTRL_FREAK hack`
- Primary files read: `apps/web/index.html` (demo UI), `README.md`, `ARCHITECTURE.md`
- Product name: QF Pipeline
- Tagline / strongest claim: TOPIC IN. MP4 OUT. Zero keys required.
- Key UI or visual moment to recreate: the demo UI — topic input with typed text, Generate button, status line, video preview + script JSON
- Copy that must appear verbatim:
  - TOPIC IN. MP4 OUT.
  - Zero keys required.
  - Same API. Same storage. Pick your runtime.
  - Ship it. Publish it on Qoneqt.

## Creative Direction
- Tone preset: default
- Creative direction: high-energy hackathon launch film
- Interpretation: playful and confident; fast motion with full reading holds; real product claims, no parody.
- Angle: Every team demos a pipeline — we ship like prod. The video proves it by showing the actual working flow, not slides about it.
- Hook: "TOPIC IN. MP4 OUT." slams in, then "Zero keys required." settles beneath.
- Outro / punchline: finished 9:16 video plays in frame; "Ship it. Publish it on Qoneqt."
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unrelated visual redesign

## Visual Identity
- Background: #0b0b12
- Text: #f2f2f5
- Accent: #ffe878
- Display font: system-ui bold (fallback: Arial/Helvetica bold)
- Body font: system-ui (fallback: Arial/Helvetica)
- Visual references from the project: gradient video cards (deep purple → blue) with white QONEQT badge + yellow caption; demo UI card (#15151f, rounded 16px)

## Storyboard
Use the storyboard in `brag-output/brag-plan.md` as the creative contract.

Scene summary:
1. Hook — 3s — "TOPIC IN. MP4 OUT." slam + "Zero keys required." settle
2. The demo — 4s — recreated demo UI: topic types in, cursor clicks Generate, status flips
3. The pipeline — 5s — SCRIPT / CARDS / FFMPEG cards arrive one by one, hold full set
4. Twin backends — 4s — PYTHON + JAVA badges, "Same API. Same storage.", 7/7 tests chip
5. Outro — 4s — finished 9:16 video plays; "Ship it. Publish it on Qoneqt."

## Audio
- Audio role: warm upbeat bed
- Audio arc: full-energy entrance → steady momentum → resolve + fade under outro
- Music: happy-beats-business-moves-vol-1-by-ende-dot-app.mp3
- Music treatment: start 0.0s full bed for the full 20s (no fade automation — out of contract without the audio skill; music ends with the video)
- Music cue guidance: no bundled preset (cues/ empty); SFX layer dropped (binaries absent from install), so no beat locks needed — motion timing stands on its own
- Audio-reactive treatment: skipped — extraction helper output format not contracted in this run; documented, render not blocked
- Audio-coupled moments: none (music bed only)
- SFX selection guidance: none — SFX binaries absent from this skill install
- SFX analysis guidance: n/a (no SFX)
- Exact SFX choice: n/a
- Audio files: music copied into `brag-output/composition/assets/music/`

## Hyperframes Instructions
Load the composition-building Hyperframes domain skills — `hyperframes-core` (composition contract + `data-*` timing), `hyperframes-animation` (motion), `hyperframes-creative` (design spec, beats, audio-reactive), `hyperframes-keyframes` (seek-safe keyframes), and `hyperframes-cli` (lint/check/render). /brag is its own workflow: do not enter the `hyperframes` entry-point intent interview and do not route into its generic promo / launch-video workflow. Prefer native Hyperframes conventions over anything in `/brag`.

Requirements:
- Show at least one real UI, copy, or visual element from the source project.
- Keep all text readable in the final render.
- Keep the video within 15-25 seconds.
- Include the planned music layer (SFX documented as unavailable).
- Treat `/brag` audio notes as guidance, not a fixed cue sheet. Choose SFX after the visual animation exists.
- Treat music cue metadata as optional timing hints. Hyperframes decides exact animation timing and should ignore cues that hurt readability, scene pacing, or the product story.
- Major reveals may move toward nearby strong cues within about 0.15s. Smaller entrances may align to nearby beat points within about 0.10s. Use only 1-3 strong cue locks in a 15-25s video unless the edit clearly benefits from more.
- Use SFX to support motion and interaction: card sounds for card-like reveals, short announcement cues for major payoffs, key/click sounds for text or user actions, and restraint when the edit is already busy.
- Honor planned music treatment such as fade-outs, ducking, beat-aligned reveals, or letting a final SFX ring over the music, using the best Hyperframes-supported implementation.
- When music is present and the treatment is not `none`, consider Hyperframes audio-reactive workflow: extract audio data and use RMS/frequency bands for subtle, brand-specific motion. Good targets are glow, depth, background warmth, card presence, title emphasis, or other existing visual elements. Avoid waveform/equalizer visuals, musical-note graphics, generic particle systems, strobing, or heavy pulsing.
- Use local assets for audio and any required runtime/media dependencies when possible.
- Run `hyperframes check` before render — it is brag's single gate.
