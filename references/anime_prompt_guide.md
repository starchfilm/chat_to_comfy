# Anime Prompt Guide

## Core Principles

1. **Tag order affects generation results** - NovelAI models are sensitive to tag order
2. **Quality tags go first** - Ensure generation baseline quality
3. **Character tag weight should be moderate** - Avoid overriding the main model's style
4. **Layered structure is clear** - Facilitates debugging and iteration
5. **Static/dynamic separation** - Fixed parts rarely change; dynamic parts are easy to swap for debugging

## Layered Template Structure

Prompts are separated into **fixed layers** and **variable layers**. When debugging, you only need to change the variable layers, not rewrite everything.

**⚠️ Character Appearance Verification Rule (Required)**

Before writing the B2 layer, you must complete these verification steps. Incorrect appearance descriptions will prevent LoRA features from being reproduced (example: guessing a character has short hair when the official design and LoRA training data both use long hair, resulting in a mismatched output).

```
Character Appearance Verification Checklist
═══════════════════════════════════════
[ ] Step 1: Check LoRA official trigger words
    - Find the LoRA detail page on Civitai/RunningHub
    - Extract hair color, hairstyle, eye color, accessory descriptions from trainedWords
    - Never guess — must use official trigger words as the source of truth

[ ] Step 2: Confirm character English name
    - Search using English name + game abbreviation
    - Example: Raiden Shogun → "Raiden Shogun Genshin"
    - Chinese names rarely return results in English resources

[ ] Step 3: Fill in B2 layer appearance description
    - Hair color/hairstyle → From LoRA trigger words, don't invent
    - Eye color → From LoRA trigger words
    - Signature accessories/features → From LoRA trigger words
    - Body type/skin tone → From LoRA trigger words

[ ] Step 4: Reference character lookup table
    - Known character official appearance descriptions are in civitai_api.md
    - These have been verified and can be used directly in the B2 layer
═══════════════════════════════════════
```

**Known Tag Pitfalls (Verified)**

| Tag | Issue | Solution |
|-----|-------|----------|
| `character sheet` + `full body` | On some checkpoints, triggers multi-person multi-angle collage | Remove these two tags for single-character portraits, use `solo` instead |
| `flushed cheeks` + `soft lighting` | In soft light environments, cheeks produce glass/plastic reflective highlights | Remove `flushed cheeks` for indoor soft scenes, add `flushed cheeks` to negative prompt |

```
═══════════════════════════════════════
【A. Image Quality】 ← Fixed Layer
═══════════════════════════════════════
masterpiece, best quality, ultra-detailed, official anime style,

═══════════════════════════════════════
【B. LoRA Trigger + Character Fixed Appearance】 ← Fixed Layer (change when switching characters)
═══════════════════════════════════════
  ┌─ B1: LoRA Trigger Words ─┐
<lora:character_lora:0.7>, character_english_name, franchise_name,
  └─────────────────────────────┘
  ┌─ B2: Character Fixed Appearance (must verify before filling) ─┐
1girl, solo, [hair_color], [hairstyle], [eye_color], [body_type],
[signature_accessories/features],
  └──────────────────────────────────────────────────────────────┘

═══════════════════════════════════════
【C. Clothing】 ← Variable Layer
═══════════════════════════════════════
# Option 1: White dress
white dress with gold trim, elegant

# Option 2: Festival outfit
layered halter dress, ribbon, arm garter, crystal pumps

# Option 3: JK uniform
white shirt, blue skirt, ribbon, sailor collar

═══════════════════════════════════════
【D. Expression】 ← Variable Layer
═══════════════════════════════════════
# Option 1: Stoic
cold expression, serious, looking at viewer

# Option 2: Gentle
gentle smile, soft eyes, blush

# Option 3: Cheerful
open mouth smile, cheerful, dynamic pose

═══════════════════════════════════════
【E. Pose/Action】 ← Variable Layer
═══════════════════════════════════════
# Option 1: Standing
standing, elegant pose, looking at viewer

# Option 2: Floating
floating, gentle movement, hair flowing

# Option 3: Sitting
sitting, hand on chin, relaxed

# Option 4: Combat
dynamic pose, combat stance, action

═══════════════════════════════════════
【F. Scene/Lighting】 ← Variable Layer
═══════════════════════════════════════
# Option 1: Cosmic sky
cosmic background, stars, floating water droplets, moonlight

# Option 2: Indoor warm light
indoors, warm lighting, window, soft shadows

# Option 3: Natural sunlight
outdoors, sunlight, forest, wind, natural

# Option 4: Festival
festival, lantern, night scene, fireworks

═══════════════════════════════════════
【G. Negative Prompt】 ← Fixed Layer
═══════════════════════════════════════
lowres, bad anatomy, bad hands, extra fingers,
missing fingers, worst quality, low quality, blurry,
deformed face, bad proportions, watermark, text,
signature, cropped, normal quality

═══════════════════════════════════════
【Optional】 Negative Embeddings (Anything series)
═══════════════════════════════════════
EasyNegative, verybadimagenegative_v1.3,
bad-hands-5, bad_prompt_version2
```

## Tag Writing Reference

### 1. Quality Tags (Fixed Layer)

```
masterpiece, best quality, high quality, ultra detailed,
absurdres, incredibly absurdres, huge filesize
```

> **Purpose**: Ensure the model outputs maximum quality, reducing bad hands, deformities, etc.

### 2. Style Tags

```
anime, anime style, colorful, vibrant colors,
detailed background, beautiful background
```

> **Purpose**: Define the visual style, distinguishing from photorealistic models

### 3. Character Tags (Fixed Layer)

```
solo, 1girl, 2girls, portrait, full body, upper body
```

> **Purpose**: Determine character count and composition

### 4. Appearance Tags (Fixed Layer)

#### Hair
```
long hair, short hair, medium hair
blonde hair, brown hair, black hair, white hair, blue hair
pink hair, red hair, purple hair, green hair, silver hair
straight hair, wavy hair, curly hair
twintails, ponytail, braid, hair bun, side bangs
```

#### Eyes
```
blue eyes, red eyes, green eyes, brown eyes, purple eyes
yellow eyes, pink eyes, orange eyes, black eyes
heterochromia, detailed eyes, beautiful detailed eyes
```

### 5. Expression Tags (Variable Layer)
```
smile, grin, open mouth, closed eyes, blush
serious, angry, sad, tears, surprised
```

### 6. Clothing Tags (Variable Layer)
```
school uniform, casual, dress, kimono, armor
jacket, shirt, skirt, pants, shorts
ribbon, necklace, earrings, gloves, boots, shoes
white shirt, black skirt, red dress, blue jacket
```

### 7. Action/Pose Tags (Variable Layer)
```
standing, sitting, walking, running, jumping
leaning, lying, dancing, jumping
arms crossed, hands on hips, looking at viewer
```

### 8. Scene Tags (Variable Layer)
```
indoors, outdoors, sky, clouds, sunset, night
city, street, forest, beach, classroom
bedroom, garden, mountain, ocean, river
```

### 9. Lighting Tags (Variable Layer)
```
backlighting, frontlighting, sidelighting
soft lighting, dramatic lighting, natural lighting
sunlight, moonlight, neon lighting
```

### 10. Camera Tags (Variable Layer)
```
dynamic angle, from above, from below
wide angle, close-up, cowboy shot
pov, dutch angle, looking at viewer
```

## Tag Weight Syntax

### Increase Weight
```
(tag:1.2)     - Increase by 20%
((tag))       - Increase by 10%
```

### Decrease Weight
```
(tag:0.8)     - Decrease by 20%
(((tag)))     - Decrease by 10%
```

### Examples
```
# Emphasize blue eyes
(blue eyes:1.3), blonde hair, smile

# Lower school uniform weight
(school uniform:0.7), 1girl
```

## Negative Prompt

### Basic Negative (Universal)
```
worst quality, low quality, normal quality
bad anatomy, bad hands, bad proportions
extra digits, fewer digits, missing fingers
missing limbs, extra limbs, floating limbs
deformed, disfigured, mutated
blurry, out of focus, lowres
text, watermark, signature, username
cropped, worst feet, extra ears
```

### Anything Series Recommended (with Embeddings)
```
nsfw, ng_deepnegative_v1_75t
bad_prompt_version2, bad-hands-5
easynegative, verybadimagenegative_v1.3
```

## Common Scene Templates

### Character Close-up
```
masterpiece, best quality, high quality, ultra detailed, absurdres
anime style, colorful
1girl, upper body
blue eyes, blonde hair, long hair, wavy hair
smile, blush
white shirt, black skirt, ribbon
indoors, classroom, window
soft lighting, from below
```

### Full Body Portrait
```
masterpiece, best quality, high quality, ultra detailed
anime style, detailed background
1girl, full body, standing
red eyes, black hair, twintails, long hair
smile, arms crossed
school uniform, white shirt, black skirt, red ribbon
outdoors, school, cherry blossoms, blue sky
sunlight, wind, dynamic angle
```

### Combat Pose
```
masterpiece, best quality, high quality, ultra detailed
anime style, action
1girl, solo, dynamic pose, full body
silver hair, ponytail, flowing hair
determined expression, combat stance
armor, weapon, cape
outdoors, battlefield, dramatic lighting, backlighting
```

## Chinese to English Quick Reference

| Chinese | English | Chinese | English |
|---------|---------|---------|---------|
| 女孩 | 1girl | 男孩 | 1boy |
| 长发 | long hair | 短发 | short hair |
| 金发 | blonde hair | 白发 | white hair |
| 黑发 | black hair | 蓝发 | blue hair |
| 微笑 | smile | 大笑 | grin |
| 校服 | school uniform | 和服 | kimono |
| 双马尾 | twintails | 马尾 | ponytail |
| 室内 | indoors | 室外 | outdoors |
| 正面 | front view | 侧面 | side view |
| 猫耳 | cat ears | 兽耳 | animal ears |

## Debugging Tips

1. **Start with basic composition** - Run without LoRA first to confirm composition is correct
2. **Add elements gradually** - Only change one tag at a time, observe changes
3. **Weight fine-tuning** - If character features aren't prominent, increase LoRA weight
4. **Fix Seed** - When comparing effects, fix the Seed
5. **Resolution matching** - Anime models recommend 512x768 or 768x512 for SD1.5, 896x1152 for SDXL/Pony
6. **Layer-based modification** - When debugging, only change variable layers (A/B/G stay fixed)
