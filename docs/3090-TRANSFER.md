# 3090 Transfer Pack — QF Pipeline video models

Two open-weight downloads live outside the git repo (too big to commit).
Copy these folders to the 3090 PC (USB/robocopy — both downloads are resumable).

## Inventory

| Folder | Contents | Size* | License |
|--------|----------|-------|---------|
| `E:\Potential-gold\heygen\TransVLM\pretrained\TransVLM-v1` | HeyGen TransVLM-Qwen3-VL-4B-Instruct checkpoint (shot-transition detection) | ~8 GB | Apache-2.0 |
| `E:\Potential-gold\models\Wan2.1-T2V-14B` | Wan 2.1 text-to-video 14B (diffusion + T5 + VAE + scheduler) | ~30–40 GB | Apache-2.0 |

*Sizes fill in when the background pull finishes. Total ≈ 40 GB. 296 GB free on E: at pull start.

`heygen/TransVLM/.gitignore` already covers `pretrained/` — weights never touch git.

## 3090 setup (24GB VRAM, CUDA)

1. **Drivers + CUDA**: NVIDIA 550+ driver, CUDA 12.4+, Python 3.11.
2. **ComfyUI** (portable zip is fine) + these custom nodes: `ComfyUI-Manager`, Wan 2.1 wrapper (via Manager search).
3. **Place weights**: point ComfyUI's `models/diffusion_models`, `models/text_encoders`, `models/vae` at the `Wan2.1-T2V-14B` folder (or copy/symlink splits in).
4. **Smoke test**: Wan 2.1 14B, 480p, 5s, ~20 steps — expect ~5–10 min on a 3090.
5. **TransVLM** (optional QC worker): Python 3.12 + CUDA torch + `inference/README.md` in the TransVLM mirror; needs the `pretrained/TransVLM-v1` folder beside it.

## QF pipeline hookup (planned, not yet built)

- New `QF_VIDEO_ENGINE` seam: `none` (today) | `wan` | `ltx`.
- When set, the pipeline POSTs scene prompts to the local ComfyUI API (`--listen 127.0.0.1 --port 8188`) and uses returned clips as scene backgrounds instead of Pollinations stills.
- Same job schema, same `/v/{id}.mp4` serving — the engine is a background swap, not a rewrite.

## Transfer command (run on this machine)

```bat
robocopy E:\Potential-gold\models <USB>:\models /MIR /Z
robocopy E:\Potential-gold\heygen\TransVLM\pretrained <USB>:\pretrained /MIR /Z
```
