# Incident Video Simulation

Generate **AI-labeled incident reconstruction videos** from case JSON using **Wan 1.3B GGUF** running locally via **ComfyUI**.

> **Disclaimer:** Output is an AI simulation for investigative review. It is **not real footage** and **must not be treated as evidence**.

## Prerequisites

- Windows with NVIDIA GPU (6 GB VRAM recommended)
- Python 3.10+
- Git
- CUDA drivers installed

## Quick Start

### 1. One-time setup

```powershell
cd incident-video

# Create CLI virtual environment
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Install ComfyUI + gguf custom node
.\scripts\setup_comfyui.ps1

# Download Wan 1.3B model files (~2 GB)
.\scripts\download_models.ps1
```

### 2. Start ComfyUI (Terminal 1)

```powershell
.\scripts\start_comfyui.ps1
```

Open http://127.0.0.1:8188 to verify it is running.

### 3. Generate video (Terminal 2)

```powershell
cd incident-video
.\.venv\Scripts\activate

# Preview prompt without generating
python -m src.generate `
  --input ..\project\dummy_case\master_case.json `
  --dry-run

# Generate simulation (outputs animated WebP by default)
python -m src.generate `
  --input ..\project\dummy_case\master_case.json `
  --output .\output\incident_simulation.webp `
  --seconds 2 --fps 15 --seed 42
```

For production pipeline output:

```powershell
python -m src.generate `
  --input ..\project\output\CASE_37e9a78cbf45553ebdbbf88e5e2ca761\processed\context\case_context.json `
  --output .\output\case_simulation.webp
```

## Multi-scene (longer, detailed) video

Multi-scene mode defaults to the **I2V pipeline** (Path B):

1. **SD 1.5 keyframe** per scene (shared visual anchor for consistency)
2. **Wan VACE 1.3B I2V** animates each keyframe with a motion prompt
3. **Last-frame chaining** — scene N's final frame becomes scene N+1's reference
4. **Crossfade stitch** into one MP4

Download the extra models first (VACE + SD 1.5 checkpoint, ~5 GB additional):

```powershell
.\scripts\download_models.ps1
```

Preview prompts:

```powershell
.\scripts\generate.ps1 `
  --input ..\project\dummy_case\master_case.json `
  --multi-scene --dry-run
```

Generate full case-study video (~35–45 min on 6GB GPU):

```powershell
.\scripts\generate.ps1 `
  --input ..\project\dummy_case\master_case.json `
  --multi-scene `
  --scene-seconds 3 `
  --output .\output\case_study_i2v.mp4 `
  --timeout-minutes 30
```

Use `--scene-seconds 3` for a **15-second** video (5 × 3s). Keep each scene at 2–3s on 6GB VRAM.

**Pipeline flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--pipeline` | `i2v` | `i2v` = keyframe + VACE I2V + frame chain; `t2v` = legacy text-to-video |
| `--no-chain` | off | Generate a fresh SD1.5 keyframe per scene instead of chaining last frames |
| `--crossfade-ms` | `200` | Crossfade between scenes (0 = hard cut) |

Legacy T2V multi-scene (no keyframes, less continuity):

```powershell
.\scripts\generate.ps1 `
  --input ..\project\dummy_case\master_case.json `
  --multi-scene --pipeline t2v `
  --output .\output\case_study_t2v.mp4
```

Scenes: victim approach → accused approach → collision → aftermath → witness response.


| Flag | Default | Description |
|------|---------|-------------|
| `--input` | required | `case_context.json` or `master_case.json` |
| `--output` | `./output/incident_simulation.webp` | Output path |
| `--seconds` | `2` | Clip length |
| `--fps` | `15` | Frames per second |
| `--seed` | `42` | Reproducibility seed |
| `--dry-run` | off | Print prompt only |
| `--comfy-url` | `http://127.0.0.1:8188` | ComfyUI server |

Use `--output file.mp4` to auto-convert via ffmpeg if installed.

## Output Files

Each run produces:

- Video file (`.webp` from ComfyUI, or `.mp4` if ffmpeg converts)
- `.metadata.json` alongside the video with prompt, seed, model, and disclaimer flags

## Model Files

Downloaded by `scripts/download_models.ps1`:

| File | Purpose |
|------|---------|
| `wan2.1_t2v_1.3b-q4_0.gguf` | Text-to-video diffusion model |
| `wan2.1-vace-1.3b-q4_0.gguf` | VACE image-to-video model (multi-scene pipeline) |
| `umt5-xxl-encoder-q4_k_m.gguf` | Text encoder |
| `pig_wan_vae_fp32-f16.gguf` | VAE decoder |
| `v1-5-pruned-emaonly.safetensors` | SD 1.5 keyframe generator |

## Project Structure

```text
incident-video/
├── scripts/           # ComfyUI setup, model download, server start
├── src/               # Python CLI (prompt builder, ComfyUI client, I2V pipeline)
├── workflows/         # wan_t2v, wan_i2v_vace, sd15_keyframe JSON workflows
├── vendor/ComfyUI/    # Local ComfyUI install (gitignored)
└── output/            # Generated videos (gitignored)
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ComfyUI is not reachable` | Run `.\scripts\start_comfyui.ps1` first |
| `Torch not compiled with CUDA` | Run `.\scripts\install_cuda_torch.ps1` |
| `infer_schema ... list[int]` on startup | Run `.\scripts\patch_comfy_kitchen.ps1` |
| `No module named 'src'` | Run from `incident-video/` or use `.\scripts\generate.ps1` |
| OOM / CUDA out of memory | Reduce `--seconds` or use `--width 384 --height 384` |
| Missing model file | Re-run `.\scripts\download_models.ps1` (downloads T2V, VACE I2V, and SD1.5) |
| Unknown node `LoaderGGUF` | Ensure calcuis gguf node is installed (`setup_comfyui.ps1`) |

## Future Work

- Optional Wan 14B quality profile
- Integration as a stage in `project/` workflow
- Web UI in `Police-AI-Assistant`
