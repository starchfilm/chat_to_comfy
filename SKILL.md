---
name: anime-aigc-workflow
description: >
  Anime AIGC creation workflow assistant. Triggers on:
  - Find reference images ("find images", "reference images", "search popular images", "find XX images")
  - Find LoRA ("find LoRA", "search LoRA", "download LoRA")
  - Generate prompts ("generate prompt", "write prompt", "reverse engineer", "create XX prompt")
  - Character intelligence ("what characters are trending", "check XXX popularity")
  - ComfyUI generation ("generate image", "create image", "run a generation", "ComfyUI", "push image")
  - Open ComfyUI ("open ComfyUI", "launch ComfyUI", "manually adjust nodes")
---

# Anime AIGC Workflow

## Core Principles

**Chinese character name → Official English name** is the key to finding LoRA. Always use the character's official English name or romaji when searching, not the Chinese name.

**Task output formats are fixed** — avoid improvising on each run.

**Character appearance must be verified**. When writing prompts, hair color, eye color, hairstyle, body type and other fixed appearance traits **must not be guessed** — search and confirm the official design first. Incorrect appearance descriptions will prevent LoRA character features from being reproduced.

## Task Dependencies

| Task | Requires Internet | Requires Local ComfyUI | No Dependencies |
|------|:-:|:-:|:-:|
| 1. Find reference images | Yes | No | |
| 2. Find LoRA | Yes | No | |
| 3. Generate prompts | No | No | Yes |
| 4. Character intelligence | Yes | No | |
| 5. ComfyUI generation | No | **Yes** | |
| 6. Open ComfyUI | No | **Yes** | |

**Users without ComfyUI**: Tasks 1–4 work fully (find images / find LoRA / generate prompts / character intelligence). Tasks 5–6 require a locally deployed ComfyUI instance.

## Task Instructions

### Task 1: Find Reference Images (Highest Priority)

**Trigger phrases**: find images, reference images, search popular images, find XX images, search XX pixiv

**Execution steps**:

1. WebSearch for `[character English name] pixiv popular 2025`
2. Extract links from PixivDaily / PixivBox / BOBOPIC / BWIKI (≥8 links)
3. Organize into a Markdown table (#, Artist, Popularity, Notes, Link)
4. Reply directly (**no screenshots, no downloads**)

**Output format**:
```
## Character Name Reference Image Links

| # | Artist | Popularity | Notes | Link |
|---|--------|------------|-------|------|
| 01 | XXX | 1000+ bookmarks | Classic white dress | [PixivDaily](url) |
| 02 | XXX | High likes | Battle version | [BOBOPIC](url) |

### Official Art
- [BWIKI Character Name](wiki_link)
```

**Note**: Provide links only, no screenshots. Users click to view.

---

### Task 2: Find LoRA

**Trigger phrases**: find LoRA, search LoRA, download LoRA, find character LoRA

**Execution steps** (strictly follow, do not skip or add steps):

1. Convert character Chinese name to official English name (see `references/civitai_api.md` for name lookup table)
2. **web_search**: `character English name LoRA civitai` and `character English name LoRA RunningHub` (search 2–3 keywords in parallel)
3. **Extract from search result snippets/titles**: LoRA name, trigger words, recommended weight, download link. **Never open any page**
4. If snippet info is insufficient (missing trigger words or weights), **search again with different keywords** like `character English name LoRA trigger words` or `character English name LoRA recommended weight`, still only reading snippets
5. Organize into output table

**Absolute prohibitions**:
- **Do not `web_fetch` any page**, including Civitai, RunningHub, LibLib, BWIKI, and all other sites
- **Do not `web_fetch` Chinese sites** (BWIKI/Moegirl/Miyoushe etc. will always time out)
- When info is insufficient, **run more web_search with different keywords**, never attempt to open pages
- Civitai REST API (`/api/v1/models`) may return 403/400 in some environments, **do not attempt** if blocked

**Search keyword combination template**:
```
Round 1 (parallel search):
  - "character_name LoRA civitai"
  - "character_name LoRA RunningHub"
  - "character_name LoRA trigger words"

Round 2 (if round 1 lacks info):
  - "character_name LoRA trigger words weight"
  - "character_name LoRA recommended weight"
  - "character_name civitai download"
```

**Output format**:
```
## LoRA Recommendations

| LoRA Name | Author | Trigger Words | Recommended Weight | Downloads | Download |
|----------|--------|--------------|-------------------|-----------|---------|
| Example Character LoRA | author_name | `trigger_word` | 0.6-0.8 | 5000+ | [Download](link) |
```

**Handling missing info**: If trigger words/weight truly cannot be found, mark as "TBC" in the table and tell the user to check the Civitai page manually. Do not fetch pages to fill gaps.

---

### Task 3: Generate Prompts

**Trigger phrases**: generate prompt, write prompt, reverse engineer, create XX prompt

**Execution**: Generate directly, no script needed. Follow the **layered template** in `references/anime_prompt_guide.md`.

**Output format**: Must use the **layered template**, separating static parts (quality / LoRA trigger + character defaults) from dynamic parts (action / expression / clothing / scene), for easy debugging.

**⚠️ Character Appearance Verification Rule (Required)**:
Before writing the B layer, search the character's official design via web_search and confirm these key appearance attributes:
- **Hair color** (e.g. light green hair, don't guess it's black)
- **Eye color** (e.g. gold eyes, don't confuse)
- **Hairstyle** (short/long/blunt bangs/bob, etc.)
- **Body type** (slender/petite, etc.)
- **Signature accessories** (hair clips, ribbons, etc.)

Search keyword examples: `"character name" hair color eye color design`
LoRA trigger word descriptions often include correct hair/eye color, usable as secondary verification.

```
═══════════════════════════════════════
【A. Image Quality】 ← Fixed
═══════════════════════════════════════
masterpiece, best quality, ultra-detailed, official anime style,

═══════════════════════════════════════
【B. LoRA Trigger + Character Fixed Appearance】 ← Change when switching characters
═══════════════════════════════════════
  ┌─ B1: LoRA Trigger Words ─┐
<lora:character_lora:0.7>, character_english_name, franchise_name,
  └─────────────────────────────┘
  ┌─ B2: Character Fixed Appearance (must verify before filling) ─┐
1girl, solo, [hair_color], [hairstyle], [eye_color], [body_type],
[signature_accessories/features],
  └──────────────────────────────────────────────────────────────┘

═══════════════════════════════════════
【C. Clothing】 ← Frequently swapped
═══════════════════════════════════════
# Option 1: School uniform  # Option 2: Stage outfit  # Option 3: Casual

═══════════════════════════════════════
【D. Expression】 ← Frequently swapped
═══════════════════════════════════════
# Option 1: Stoic  # Option 2: Smile  # Option 3: Dark

═══════════════════════════════════════
【E. Pose/Action】 ← Frequently swapped
═══════════════════════════════════════
# Option 1: Standing  # Option 2: Sitting  # Option 3: Performing

═══════════════════════════════════════
【F. Scene/Lighting】 ← Frequently swapped
═══════════════════════════════════════
# Option 1: Indoor  # Option 2: Stage  # Option 3: Outdoor

═══════════════════════════════════════
【G. Negative Prompt】 ← Fixed
═══════════════════════════════════════
lowres, bad anatomy, bad hands, extra fingers,
missing fingers, worst quality, low quality, blurry,
deformed face, bad proportions, watermark
```

---

### Task 4: Character Intelligence

**Trigger phrases**: what characters are trending, check XXX popularity, character popularity ranking

**Execution**: WebSearch to aggregate popularity data from Xiaohongshu / X / Pinterest

---

### Task 5: ComfyUI Image Generation

**Trigger phrases**: generate image, create image, run a generation, generate one, help me generate, push image, ComfyUI

**Prerequisites**: User's local ComfyUI must be running (http://127.0.0.1:8188). AI cannot remotely start ComfyUI.

**Execution**: Call `scripts/comfyui_generate.py` to submit a workflow via the ComfyUI REST API.

**Configurable parameters**:
- Checkpoint (`--checkpoint`): default from config.json
- LoRA chaining (`--lora`): 1–3 LoRAs. Common combinations:
  - Style/detail LoRA + character LoRA (2 LoRAs)
  - Style LoRA + character LoRA + character LoRA boost (3 LoRAs)
- Positive prompt (`--positive`)
- Negative prompt (`--negative`)
- Resolution (`--width` / `--height`)
- HiRes fix toggle (`--no-hires` to disable)
- Sampling steps / CFG / sampler etc.

**Script usage examples**:
```bash
# Minimal: just change prompt and character LoRA (no workflow save, image only)
python comfyui_generate.py \
  --positive "1girl, solo, long blue hair, blue eyes, white dress, gentle smile, cherry blossoms" \
  --lora "your_character_lora.safetensors" 0.8 0.8 \
  --filename-prefix "character_sakura" \
  --copy-to-workspace

# 2 LoRAs (style + character)
python comfyui_generate.py \
  --positive "1girl, solo, long blue hair, blue eyes, white dress" \
  --lora "your_style_lora.safetensors" 1.0 1.0 \
  --lora "your_character_lora.safetensors" 0.8 0.8 \
  --filename-prefix "character" \
  --copy-to-workspace

# Change checkpoint
python comfyui_generate.py \
  --checkpoint "your_model.safetensors" \
  --positive "..." --lora "..." --copy-to-workspace

# Skip HiRes fix (fast preview)
python comfyui_generate.py \
  --positive "..." --lora "..." --no-hires --copy-to-workspace

# Want to manually adjust → add --save-workflow to save JSON
python comfyui_generate.py \
  --positive "..." --lora "..." \
  --save-workflow --copy-to-workspace

# List available models
python comfyui_generate.py --list-checkpoints
python comfyui_generate.py --list-loras

# Check if ComfyUI is online
python comfyui_generate.py --check-status
```

**`--save-workflow` purpose**: Saves the workflow JSON to the `comfyui-output/` subdirectory. Users can import it in ComfyUI via "Load API" and manually fine-tune nodes. **Not saved by default**; only generated when `--save-workflow` is added. This bridges "AI auto-generation → user manual fine-tuning".

**`--copy-to-workspace` purpose**: Copies generated images from the ComfyUI output directory to the `comfyui-output/` subdirectory (doesn't pollute workspace root). This allows AI to display images in the IDE.

**All ComfyUI outputs stored in `{workspace}/comfyui-output/`**:
- Images: `comfyui-output/character_test_00001_.png`
- Workflow JSON: `comfyui-output/character_test_workflow.json` (only with `--save-workflow`)

Not satisfied and want to manually adjust? Two steps:
1. Tell the AI "not satisfied, I want to manually adjust" → AI saves workflow JSON + opens ComfyUI interface
2. In ComfyUI, "Load API" to import the JSON → manually fine-tune nodes

**Workflow template description**:
- Built on a standard anime generation topology
- Node chain: Checkpoint → LoRA #1 (style) → LoRA #2 (character) → [LoRA #3 (optional)] → CLIP → KSampler → Tiled VAE Decode → ESRGAN Upscale → ImageScale → Tiled VAE Encode → KSampler #2 (HiRes) → VAE Decode → SaveImage
- Reroute nodes don't work in API mode, connections are direct
- Tiled VAE decoding (tile 512, overlap 64), 8GB VRAM friendly

---

### Task 6: Open ComfyUI Interface

**Trigger phrases**: open ComfyUI, launch ComfyUI, manually adjust nodes, open workflow interface

**Execution**: Open ComfyUI Web UI in browser for manual node adjustment.

```bash
# macOS/Linux
open http://127.0.0.1:8188

# Windows
start http://127.0.0.1:8188

# Linux (alternative)
xdg-open http://127.0.0.1:8188
```

If ComfyUI is not running, remind the user to start it first.

---

## Reliable Sources

- BWIKI (wiki.biligame.com): Character art
- PixivDaily (pixivdaily.com): Pixiv illustration mirror
- PixivBox (pixivbox.com): Pixiv mirror
- BOBOPIC (bobopic.com): Pixiv curated
- RunningHub (runninghub.cn): LoRA downloads (China)
- TensorHub (tensorhub.art): Model mirror
- LibLib (liblib.art): LoRA downloads

## Blocked Sources (Avoid)

- Fandom Wiki (Cloudflare blocking)
- Huaban (anti-scraping)
- Pixivision (anti-scraping)

## Anti-Timeout Rules (Important)

**Fundamental principle: search only, never fetch. `web_fetch` is the primary cause of timeouts.**

**Do not use `web_fetch` on any Chinese Wiki / game guide site / community page.** These sites (BWIKI, Moegirl, Miyoushe, Tieba, Bilibili, etc.) have complex, slow-loading pages that will always time out with `web_fetch`.

**Also do not `web_fetch` Civitai / RunningHub / LibLib or other LoRA download sites.** These will also time out or return empty pages.

**Civitai REST API (`/api/v1/models`) may return 403/400 in some environments, do not attempt.**

**Information retrieval principle: search only, never fetch.**
- Character appearance info: Extract from `web_search` snippets, good enough is good enough
- LoRA details: Extract trigger words/weights/download links from search result titles and summaries
- Reference image links: Take URLs directly from search results, no need to open pages for verification
- If search results aren't detailed enough, **run more searches with different keywords** rather than fetching pages
- When info truly cannot be found, mark as "TBC" in output for user to check manually, don't fetch to fill gaps

**There is no scenario that permits web_fetch in AI assistant environments with timeout constraints.**

---

## Reference Resources

### references/
- `references/anime_prompt_guide.md` - Tag writing guide + layered template
- `references/civitai_api.md` - Civitai API docs + search strategies
- `references/workflow_guide.md` - Workflow operation manual

## Quick Reference

| Task | Execution |
|------|-----------|
| Find reference images | WebSearch → organize link table → reply directly (no screenshots) |
| Find LoRA | web_search with parallel keywords → extract from snippets (no web_fetch, no page fetching) |
| Generate prompts | Follow anime_prompt_guide.md layered template, generate directly |
| Character intelligence | WebSearch from multiple angles → popularity analysis + LoRA availability |
| ComfyUI generation | comfyui_generate.py → API submit → wait for result → copy images |
| Open ComfyUI | Open `http://127.0.0.1:8188` in browser |
