# Anime AIGC Workflow

An AI-powered anime image generation workflow skill for [WorkBuddy](https://www.codebuddy.cn/) (or any OpenClaw-compatible AI coding assistant). Search reference images, find LoRA models, craft structured prompts, and generate images via ComfyUI API — all through natural language.

> **How it works**: This is NOT a standalone application. It is a **skill pack** that teaches an AI agent how to help you with anime image generation. The agent reads `SKILL.md` to understand when and how to act, then calls the Python scripts in `scripts/` to interact with your local ComfyUI. You need an AI assistant that supports the skill system (currently WorkBuddy / CodeBuddy) + a locally running ComfyUI instance.

## Features

- **Find Reference Images** — Search Pixiv mirrors and anime wikis for character reference art
- **Find LoRA** — Search Civitai / RunningHub / LibLib for character LoRA models, with trigger words and recommended weights
- **Generate Prompts** — Layered prompt template system (static vs. dynamic layers) for efficient iteration
- **Character Intelligence** — Lookup trending characters and official appearance data
- **ComfyUI Integration** — Submit workflows via REST API, with HiRes fix, multi-LoRA chaining, and workflow JSON export for manual fine-tuning

## Prerequisites

| Task | Requires Internet | Requires Local ComfyUI |
|------|:-:|:-:|
| Find reference images | Yes | No |
| Find LoRA | Yes | No |
| Generate prompts | No | No |
| Character intelligence | Yes | No |
| ComfyUI image generation | No | **Yes** |
| Open ComfyUI UI | No | **Yes** |

Users without ComfyUI can still use tasks 1–4. Tasks 5–6 require a local ComfyUI instance running at `http://127.0.0.1:8188`.

## Installation

### Option 1: Install as a WorkBuddy Skill

Copy this entire directory to your WorkBuddy skills folder:

```bash
# User-level skill (available across all projects)
cp -r anime-aigc-workflow/ ~/.workbuddy/skills/anime-aigc-workflow/

# Or project-level skill (shared with team)
cp -r anime-aigc-workflow/ .workbuddy/skills/anime-aigc-workflow/
```

### Option 2: Use scripts standalone

The scripts in `scripts/` can be used independently:

```bash
# Generate an image via ComfyUI API
python scripts/comfyui_generate.py --positive "1girl, solo, ..." --lora "your_lora.safetensors" 0.8 0.8

# Search LoRA on Civitai
python scripts/search_lora.py "Hatsune Miku"

# Generate structured prompts
python scripts/generate_prompt.py "blue hair girl, smile, twintails, indoors"
```

## Configuration

Copy `config.example.json` to `config.json` and customize:

```json
{
  "comfyui_url": "http://127.0.0.1:8188",
  "default_checkpoint": "your_model.safetensors",
  "default_lora": "your_style_lora.safetensors",
  "default_style_artists": "your, artist, tags",
  "default_negative_embeddings": "embedding:EasyNegative, embedding:badhandv4",
  "default_width": 896,
  "default_height": 1152,
  "default_steps": 30,
  "default_cfg": 7.0,
  "hires_fix": true,
  "hires_steps": 10,
  "hires_denoise": 0.3,
  "upscale_model": "RealESRGAN_x4plus_anime_6B.pth"
}
```

Alternatively, set environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `COMFYUI_URL` | ComfyUI API endpoint | `http://127.0.0.1:8188` |
| `COMFYUI_OUTPUT_DIR` | ComfyUI output directory (auto-detected if empty) | *(auto)* |
| `WORKSPACE_DIR` | Your workspace root | Current directory |

## Usage (as WorkBuddy Skill)

Once installed, just talk to your AI assistant in natural language:

| Say this | Triggers |
|----------|----------|
| "Find reference images of Hatsune Miku" | Reference image search |
| "Find LoRA for Raiden Shogun" | LoRA search |
| "Generate a prompt for a blue-haired girl in a school uniform" | Prompt generation |
| "What anime characters are trending?" | Character intelligence |
| "Generate an image of Miku" / "Run ComfyUI" | ComfyUI image generation |
| "Open ComfyUI" / "Let me manually adjust" | Open ComfyUI Web UI |

## Prompt Layering System

The prompt template separates **static layers** (rarely change) from **dynamic layers** (change per image), making iteration efficient:

```
[A. Quality]           ← Fixed: masterpiece, best quality, ...
[B. LoRA + Character]  ← Fixed per character: trigger words + official appearance
[C. Clothing]          ← Dynamic: swap per image
[D. Expression]        ← Dynamic: swap per image
[E. Pose/Action]       ← Dynamic: swap per image
[F. Scene/Lighting]    ← Dynamic: swap per image
[G. Negative Prompt]   ← Fixed: quality filters
```

See `references/anime_prompt_guide.md` for the complete template and tag reference.

## ComfyUI Workflow Topology

```
Checkpoint → LoRA #1 (style) → LoRA #2 (character) → [LoRA #3 (optional)]
    → CLIP Text Encode (positive/negative)
    → KSampler #1 (main generation)
    → Tiled VAE Decode (8GB VRAM friendly)
    → ESRGAN Upscale
    → ImageScale
    → Tiled VAE Encode
    → KSampler #2 (HiRes fix)
    → VAE Decode → Save Image
```

Key features:
- **Tiled VAE** (tile 512, overlap 64) — works on 8GB VRAM
- **Multi-LoRA chaining** — up to 3 LoRAs in series
- **HiRes fix** — ESRGAN 4x upscale + second pass sampling
- **Workflow export** — save JSON for manual fine-tuning in ComfyUI ("Load API")

## Project Structure

```
anime-aigc-workflow/
├── SKILL.md                      # Skill definition (triggers + instructions)
├── README.md                     # This file
├── LICENSE                       # MIT License
├── config.example.json           # Configuration template
├── assets/
│   └── workflow_template.json    # ComfyUI workflow template reference
├── references/
│   ├── anime_prompt_guide.md     # Tag writing guide + layered template
│   ├── civitai_api.md            # Civitai API docs + search strategies
│   └── workflow_guide.md         # ComfyUI workflow operation manual
└── scripts/
    ├── comfyui_generate.py       # ComfyUI API submission script
    ├── generate_prompt.py        # Prompt generator (Chinese→English tag mapping)
    └── search_lora.py            # Civitai LoRA search script
```

## Key Principles

1. **Chinese character name → Official English name** is the key to finding LoRA. Always use the character's official English name or romaji when searching.
2. **Verify character appearance** before writing prompts. Never guess hair color, eye color, or accessories — search the official design first.
3. **Only search, never fetch**. In AI assistant environments, `web_fetch` on complex pages (Wikis, Civitai, etc.) often times out. Use `web_search` with multiple keyword variations instead.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Areas of particular interest:

- Additional LoRA source integrations
- Cross-platform ComfyUI path detection improvements
- More character name lookup tables
- WebUI (Automatic1111/Forge) API support

## License

[MIT](LICENSE)
"# chat_to_comfy" 
