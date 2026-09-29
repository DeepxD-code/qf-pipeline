# 3090 Transfer Pack — QF Pipeline video models

Two open-weight downloads live outside the git repo (too big to commit).

## Inventory (measured, not estimated)

| Folder | Contents | Size | License | State |
|--------|----------|------|---------|-------|
| `E:\Potential-gold\heygen\TransVLM\pretrained\TransVLM-v1` | TransVLM-Qwen3-VL-4B-Instruct (shot-transition detection) | 9.01 GB | Apache-2.0 | **complete** |
| `E:\Potential-gold\models\Wan2.1-T2V-14B` | Wan 2.1 T2V 14B | **69.10 GB** total | Apache-2.0 | **18.85 GB (2 of 6 shards) + VAE** |

Wan 2.1 T2V 14B breakdown, because it drives USB and disk planning:

| File | Size |
|---|---|
| `models_t5_umt5-xxl-enc-bf16.pth` (T5 text encoder) | 11.36 GB |
| `diffusion_pytorch_model-0000{1..6}-of-00006.safetensors` | ~9.9 GB each ≈ 59 GB |
| `Wan2.1_VAE.pth` | 0.51 GB |

Budget **70 GB** of USB and **~75 GB** of free space on the 3090, not 40.

## Throughput warning

Measured from this laptop: **0.29 MB/s** to `us.aws.cdn.hf.co` (metadata
endpoints are fine at ~1.7 s; the file CDN is the bottleneck). At that rate the
remaining ~50 GB is a **~49 hour** transfer, and it stalls entirely under load.

Prefer downloading directly on the 3090 PC if its connection is better — that
machine runs the model anyway. If downloading here:

```bash
python scripts/download_models.py     # detached-safe, retries + resume
python scripts/check_wan.py           # verify no shard is truncated
```

`check_wan.py` matters: an interrupted shard keeps a valid safetensors header,
so file size alone will not tell you the copy is whole.

## 3090 setup (24GB VRAM, CUDA)

1. **Drivers + CUDA**: NVIDIA 550+ driver, CUDA 12.4+, Python 3.11.
2. **ComfyUI** (portable zip is fine) + `ComfyUI-Manager` + the Wan 2.1 wrapper
   (install via Manager search).
3. **Place weights**: point ComfyUI's `models/diffusion_models`,
   `models/text_encoders` and `models/vae` at the `Wan2.1-T2V-14B` folder.
4. **Smoke test**: Wan 2.1 14B, 480p, 5s, ~20 steps — expect ~5–10 min on a 3090.
5. **TransVLM** (optional QC worker): Python 3.12 + CUDA torch + `inference/README.md` in the TransVLM mirror; needs the `pretrained/TransVLM-v1` folder beside it.

## QF pipeline hookup (planned, not yet built)

- New `QF_VIDEO_ENGINE` seam: `none` (today) | `wan` | `ltx`.
- When set, the pipeline POSTs scene prompts to the local ComfyUI API (`--listen 127.0.0.1 --port 8188`) and uses returned clips as scene backgrounds instead of Pollinations stills.
- Same job schema, same `/v/{id}.mp4` serving — the engine is a background swap, not a rewrite.

## Verify before and after transfer

Downloads get interrupted, and a short-truncated safetensors shard still has a
valid JSON header — so file size alone will not tell you the copy is whole.
`scripts/check_wan.py` reads each shard's header and checks the declared tensor
byte ranges fit inside the file:

```bash
python scripts/check_wan.py                                     # default local path
WAN_DIR=/mnt/models/Wan2.1-T2V-14B python scripts/check_wan.py  # on the 3090
```

A good shard reports `ok 189 tensors`; a truncated one reports
`truncated: needs 9.89GB, has 6.20GB`. Re-download just the bad file:

```bash
huggingface-cli download Wan-AI/Wan2.1-T2V-14B diffusion_pytorch_model-00004-of-00006.safetensors
```

## Transfer command (run on this machine)

```bat
robocopy E:\Potential-gold\models <USB>:\models /MIR /Z
robocopy E:\Potential-gold\heygen\TransVLM\pretrained <USB>:\pretrained /MIR /Z
```
