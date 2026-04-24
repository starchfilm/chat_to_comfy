# AIGC Creation Workflow Operation Manual

## Task Output Specifications

```
Task Type          │  Trigger Phrases              │  Output
───────────────────┼───────────────────────────────┼─────────────────────────────
1. Find Images     │ find images/reference images   │ Link table (no screenshots)
2. Find LoRA      │ find LoRA/download LoRA        │ Download link + trigger words + weight
3. Generate Prompt │ generate prompt/reverse engineer│ Layered structure prompt template
4. Character Intel │ character popularity/ranking    │ Popularity report
5. ComfyUI Gen    │ generate image/ComfyUI/push    │ Submit → wait → images + workflow JSON
6. Open ComfyUI   │ open ComfyUI/manually adjust   │ Browser opens UI
```

## Step 1: Find Reference Images (Links Only, No Screenshots)

### Source Priority

1. **PixivDaily** (pixivdaily.com) - Highest priority, stable mirror
2. **PixivBox** (pixivbox.com) - Mirror site, accessible
3. **BOBOPIC** (bobopic.com) - Curated site, has popularity data
4. **BWIKI** (wiki.biligame.com) - Official character art

### Execution Flow

1. **Search**: WebSearch `[character name] pixiv popular 2025`, extract ≥8 links
2. **Organize table**: # / Artist / Popularity / Notes / Link
3. **Reply directly**: Markdown table, no screenshots

### Image Collection Template

```markdown
## Character Name Reference Image Links

| # | Artist | Popularity | Notes | Link |
|---|--------|------------|-------|------|
| 01 | XXX | 1000+ bookmarks | Classic white dress | [PixivDaily](https://pixivdaily.com/?pid=123456) |
| 02 | XXX | High likes | Battle version | [BOBOPIC](https://bobopic.com/xxx.html) |

### Official Art
- [BWIKI Character Name](https://wiki.biligame.com/sr/CharacterName)
```

**Note**: No screenshots, no downloads, no deliver_attachments. Users click links to view.

## Step 2: Find LoRA

### Execution Method (Only method: web_search, web_fetch is prohibited)

1. Chinese character name → Official English name (see `civitai_api.md` lookup table)
2. Parallel web_search 2-3 keywords: `character_name LoRA civitai`, `character_name LoRA RunningHub`, `character_name LoRA trigger words`
3. Extract info from search snippets/titles directly, **never open pages**
4. If info is insufficient, search with different keywords, don't fetch

**Civitai REST API may be unavailable** (returns 403/400 in some environments), do not attempt.

**Absolutely no web_fetch of any page.**

### Search Keyword Rules

| Chinese Name | English Name | Search Keywords |
|-------------|-------------|-----------------|
| 雷电将军 | Raiden Shogun | `Raiden Genshin` |
| 初音未来 | Hatsune Miku | `Miku Vocaloid` |
| 流萤 | Firefly | `Firefly HSR` |

See `civitai_api.md` for the character name lookup table.

### LoRA Selection Criteria

| Metric | Preferred | Notes |
|--------|-----------|-------|
| Downloads | > 5,000 (> 10,000 preferred) | Too low may be unstable |
| Rating | > 4.5/5 | Reference community evaluation |
| Base Model | Match your main model | SD 1.5 / SDXL / Illustrious / Pony |
| Trigger Words | Clean and concise | Avoid overly long trigger word lists |

### LoRA Output Format

```markdown
## LoRA Recommendations

| LoRA Name | Author | Trigger Words | Recommended Weight | Download |
|----------|--------|--------------|-------------------|---------|
| Character Name LoRA | author_name | `trigger_word` | 0.6-0.8 | [Download](link) |
```

## Step 3: Generate Prompts

Follow the **layered template** in `anime_prompt_guide.md` to generate directly.

**Core concept**: Separate prompts into fixed and variable layers:

- **Fixed layers** (A. Image Quality / B. LoRA trigger + character design / G. Negative prompt): Change when switching characters or base settings
- **Variable layers** (C. Clothing / D. Expression / E. Pose / F. Scene/Lighting): Swap per image as needed

## Step 4: ComfyUI Image Generation

**Prerequisite**: ComfyUI must be running locally (http://127.0.0.1:8188). AI cannot start it remotely.

### Universal Generation Script

Script location: `scripts/comfyui_generate.py`

### Workflow Topology

```
[1] CheckpointLoaderSimple (main model)
         ↓ MODEL, CLIP, VAE
[30] LoraLoader #1 (style/detail LoRA)
         ↓ MODEL, CLIP
[33] LoraLoader #2 (character LoRA)
         ↓ MODEL, CLIP
[21] LoraLoader #3 (optional boost)
         ↓ MODEL, CLIP
[3]  CLIPTextEncode (positive)
[4]  CLIPTextEncode (negative)
         ↓
[6]  EmptyLatentImage (896×1152)
         ↓
[5]  KSampler #1 (euler, 30 steps, CFG 7.0)
         ↓
[10] VAEDecodeTiled (tile 512, overlap 64)
         ↓
[18] PreviewImage
[12] ImageUpscaleWithModel (ESRGAN 4x)
         ↓
[13] ImageScale → 1472×1856
         ↓
[14] VAEEncodeTiled
         ↓
[15] KSampler #2 (euler, 10 steps, denoise 0.3)
         ↓
[7]  VAEDecode
         ↓
[9]  SaveImage
```

**Note**: Reroute nodes don't work in API mode, use direct connections.

### Configurable Parameters

| Parameter | CLI Flag | Default | Description |
|-----------|---------|---------|-------------|
| Checkpoint | `--checkpoint` | From config.json | View with `--list-checkpoints` |
| LoRA | `--lora` (repeatable) | From config.json | Format: name model_strength clip_strength |
| Positive prompt | `--positive` | (required) | Style artists auto-prepended |
| Negative prompt | `--negative` | Default long string | Includes badhandv4, easynegative |
| Resolution | `--width` / `--height` | 896 / 1152 | Portrait ratio |
| Sampling steps | `--steps` | 30 | Main generation |
| CFG | `--cfg` | 7.0 | |
| HiRes fix | `--no-hires` to disable | Enabled by default | ESRGAN 4x + second pass sampling |
| HiRes steps | `--hires-steps` | 10 | |
| HiRes denoise | `--hires-denoise` | 0.3 | Higher = more repaint |
| Seed | `--seed` | Random | -1=random |
| Output prefix | `--filename-prefix` | ComfyUI | |
| Save workflow | `--save-workflow` | No | Save JSON, importable via ComfyUI Load API |
| Copy to workspace | `--copy-to-workspace` | No | |

### Bridging "AI Generation" to "Manual Fine-Tuning"

1. AI calls `comfyui_generate.py` to generate (no workflow JSON saved by default)
2. If unsatisfied, tell AI "I want to manually adjust" → AI re-runs with `--save-workflow`
3. The generated `{prefix}_workflow.json` is saved to `comfyui-output/` subdirectory
4. When unsatisfied:
   - Option A: In ComfyUI, "Load API" to import the JSON and manually fine-tune nodes
   - Option B: Tell AI to adjust parameters (swap LoRA, change weights, edit prompts) and re-run
5. To open ComfyUI interface: Open `http://127.0.0.1:8188` in browser

### Quick Reference

```bash
# Check if ComfyUI is online
python comfyui_generate.py --check-status

# List available checkpoints
python comfyui_generate.py --list-checkpoints

# List available LoRAs
python comfyui_generate.py --list-loras

# Standard generation (style + character dual LoRA, HiRes fix)
python comfyui_generate.py \
  --positive "1girl, solo, long blue hair, blue eyes, white dress, gentle smile, cherry blossoms" \
  --lora "your_style_lora.safetensors" 1.0 1.0 \
  --lora "your_character_lora.safetensors" 0.8 0.8 \
  --filename-prefix "character_sakura" \
  --save-workflow --copy-to-workspace

# Quick preview (no HiRes fix, ~30s output)
python comfyui_generate.py \
  --positive "1girl, solo, ..." \
  --lora "your_character_lora.safetensors" 0.8 0.8 \
  --no-hires --copy-to-workspace

# Open ComfyUI interface for manual adjustment
# macOS:
open http://127.0.0.1:8188
# Windows:
start http://127.0.0.1:8188
# Linux:
xdg-open http://127.0.0.1:8188
```

### Standard Workflow

```
Load Checkpoint (main model)
    ↓
Load LoRA (character LoRA)
    ↓
CLIP Text Encode (positive prompt)
    ↓
CLIP Text Encode (negative prompt)
    ↓
KSampler (sampling settings)
    ↓
Save Image (output)
```

### Recommended Parameters

| Parameter | Recommended | Notes |
|-----------|-------------|-------|
| Sampling steps | 28-35 | More steps = more detail, but slower |
| CFG Scale | 7-9 | Too high = distortion, too low = blur |
| Sampler | DPM++ 2M Karras / Euler a | Quality and speed balance |
| Resolution | 512x768 / 768x512 (SD1.5) | Anime optimal ratio (portrait) |
|  | 896x1152 (SDXL/Pony/Illustrious) | SDXL-class optimal ratio |
| LoRA weight | 0.6-0.8 | Too high = artifact, too low = character doesn't resemble |

### Output Quality Checklist

- [ ] Character features correct (hair color, eyes, clothing)
- [ ] Composition as expected (full body / close-up)
- [ ] Background harmonious
- [ ] No deformities (hands, feet, proportions)
- [ ] Overall image quality satisfactory

## Common Issues and Solutions

### Q1: LoRA effect not visible
- Increase weight to 0.8-1.0
- Verify trigger words are correct
- Confirm main model is compatible with LoRA

### Q2: Deformity issues
- Add more negative prompt tags
- Lower CFG to 6-7
- Use negative embeddings

### Q3: Character features lost
- Lower LoRA weight
- Add character features to positive prompt
- Use a stronger character LoRA

### Q4: Background inconsistent
- Specify the scene in the positive prompt
- Use ControlNet for composition control
- Add a background-related LoRA

## Efficiency Tips

1. **Template reuse**: Save commonly used layered prompt templates for quick swapping
2. **Tag library**: Build a personal tag library with frequently used expressions
3. **Layered debugging**: Adjust composition first (without LoRA), then add LoRA, then fine-tune weights

## Anti-Timeout Rules (Strictly Follow)

**Fundamental principle: search only, never fetch. `web_fetch` is the primary cause of timeouts.**

**Completely prohibit `web_fetch`, no exceptions.** Including Chinese sites and English sites.

### Sites where web_fetch is absolutely prohibited (all, no exceptions)
- BWIKI (wiki.biligame.com) — Page too large, always times out
- Moegirl (mzh.moegirl.org.cn) — Same
- Miyoushe (miyoushe.com / bbs.mihoyo.com) — Complex SPA, cannot parse
- Baidu Tieba (tieba.baidu.com) — Same
- Bilibili (bilibili.com) — Same
- Zhihu (zhihu.com) — Anti-scraping + complex page
- Any Chinese Wiki / guide site / community
- Civitai (civitai.com) — Will time out or return empty page
- RunningHub (runninghub.cn) — Same
- LibLib (liblib.art) — Same
- CivArchive (civarchive.com) — Same

### Civitai REST API May Be Unavailable
- `https://civitai.com/api/v1/models` may return 403/400
- Do not attempt to call via curl or Python if blocked

### Alternatives
| Original Need | Wrong Approach | Correct Approach |
|--------------|----------------|-----------------|
| Character appearance | web_fetch BWIKI | web_search multiple times, extract from snippets |
| LoRA details | web_fetch Civitai page | web_search for trigger words and weights, extract from snippets |
| Reference image verification | web_fetch open link | Take URLs directly from search results, no verification |
| Character intelligence | web_fetch guide pages | web_search from multiple angles |
| Missing info | web_fetch to fill gaps | Mark as "TBC", let user check manually |
