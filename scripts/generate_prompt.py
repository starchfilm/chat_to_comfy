#!/usr/bin/env python3
"""
ComfyUI Anime Prompt Generator
Anime-style prompt generator based on NovelAI/Anything best practices
Supports layered Tag structure optimization, auto-generates positive/negative prompts
"""

import sys
import re
from typing import Optional


# ============================================================
# NovelAI / Anything series recommended Tag layered structure
# ============================================================

QUALITY_TAGS = [
    "masterpiece", "best quality", "high quality", "ultra detailed",
    "absurdres", "incredibly absurdres", "huge filesize"
]

STYLE_TAGS = [
    "anime", "anime style", "colorful", "vibrant colors",
    "detailed background", "beautiful background"
]

CHARACTER_TAGS = []  # Character tags, specified by user or reverse-engineered

ACTION_POSE_TAGS = [
    "solo", "1girl", "2girls", "portrait", "full body", "upper body",
    "standing", "sitting", "walking", "running", "jumping"
]

EXPRESSION_TAGS = [
    "smile", "grin", "open mouth", "closed eyes", "blush",
    "serious", "angry", "sad", "tears", "surprised"
]

HAIR_TAGS = [
    "long hair", "short hair", "medium hair",
    "blonde hair", "brown hair", "black hair", "white hair", "blue hair",
    "pink hair", "red hair", "purple hair", "green hair",
    "straight hair", "wavy hair", "curly hair",
    "long hair", "twintails", "ponytail", "braid", "hair bun"
]

EYES_TAGS = [
    "blue eyes", "red eyes", "green eyes", "brown eyes", "purple eyes",
    "yellow eyes", "pink eyes", "orange eyes", "black eyes", "heterochromia",
    "detailed eyes", "beautiful detailed eyes"
]

CLOTHING_TAGS = [
    "school uniform", "casual", "dress", "kimono", "armor",
    "jacket", "shirt", "skirt", "pants", "shorts",
    "white shirt", "black skirt", "red dress", "blue jacket",
    "ribbon", "necklace", "earrings", "gloves", "boots", "shoes"
]

SCENE_TAGS = [
    "indoors", "outdoors", "sky", "clouds", "sunset", "night",
    "city", "street", "forest", "beach", "classroom",
    "bedroom", "garden", "mountain", "ocean", "river"
]

LIGHTING_TAGS = [
    "backlighting", "frontlighting", "sidelighting",
    "soft lighting", "dramatic lighting", "natural lighting",
    "sunlight", "moonlight", "neon lighting"
]

CAMERA_TAGS = [
    "dynamic angle", "from above", "from below",
    "wide angle", "close-up", "cowboy shot",
    "pov", "dutch angle", "looking at viewer"
]

NEGATIVE_TAGS_NOVELAI = [
    "worst quality", "low quality", "normal quality",
    "bad anatomy", "bad hands", "bad proportions",
    "extra digits", "fewer digits", "missing fingers",
    "missing limbs", "extra limbs", "floating limbs",
    "deformed", "disfigured", "mutated",
    "blurry", "out of focus", "lowres",
    "text", "watermark", "signature", "username",
    "cropped", "worst feet", "extra ears"
]

NEGATIVE_TAGS_ANYTHING = [
    "nsfw", "ng_deepnegative_v1_75t",
    "bad_prompt_version2", "bad-hands-5",
    "easynegative", "verybadimagenegative_v1.3"
]


def clean_tag(tag: str) -> str:
    """Clean Tag, remove extra spaces and brackets"""
    tag = tag.strip()
    tag = re.sub(r'\s+', ' ', tag)
    return tag


def weight_tag(tag: str, weight: float) -> str:
    """
    Add weight to Tag
    weight > 1.0: increase weight (tag:1.2)
    weight < 1.0: decrease weight (tag:0.8)
    """
    if weight != 1.0:
        return f"({tag}:{weight:.1f})"
    return tag


def generate_from_description(
    description: str,
    include_lora: Optional[str] = None,
    lora_weight: float = 0.7,
    use_anything: bool = False
) -> tuple[str, str]:
    """
    Generate positive and negative prompts from text description

    Args:
        description: Character/scene description (Chinese or English)
        include_lora: LoRA name (optional)
        lora_weight: LoRA weight
        use_anything: Whether to use Anything-style Negative Embedding

    Returns:
        (positive_prompt, negative_prompt)
    """
    # Auto-translate common Chinese keywords to English Tags
    chinese_map = {
        "女孩": "1girl", "男孩": "1boy",
        "长发": "long hair", "短发": "short hair",
        "金发": "blonde hair", "白发": "white hair", "黑发": "black hair",
        "蓝眼": "blue eyes", "红眼": "red eyes", "绿眼": "green eyes",
        "微笑": "smile", "大笑": "grin",
        "站姿": "standing", "坐姿": "sitting",
        "正面": "front view", "侧面": "side view",
        "室内": "indoors", "室外": "outdoors",
        "动漫": "anime style", "写实": "realistic",
        "校服": "school uniform", "和服": "kimono",
        "双马尾": "twintails", "马尾": "ponytail",
        "猫耳": "cat ears", "兽耳": "animal ears"
    }

    # Convert Chinese description to English Tags
    converted_tags = []
    for cn, en in chinese_map.items():
        if cn in description:
            converted_tags.append(en)

    # Base quality tags
    positive_parts = QUALITY_TAGS.copy()

    # Style tags
    if "写实" in description or "realistic" in description.lower():
        positive_parts.append("realistic")
    else:
        positive_parts.append("anime style")

    positive_parts.append("colorful")

    # Add tags converted from description
    positive_parts.extend(converted_tags)

    # Scene tags (if description includes them)
    scene_keywords = ["室内", "室外", "天空", "海边", "森林", "城市", "教室", "卧室", "花园"]
    cn_to_en = {
        "室内": "indoors", "室外": "outdoors", "天空": "sky", "海边": "beach",
        "森林": "forest", "城市": "city", "教室": "classroom",
        "卧室": "bedroom", "花园": "garden"
    }
    for kw in scene_keywords:
        if kw in description and kw in cn_to_en:
            positive_parts.append(cn_to_en[kw])

    # LoRA tags
    if include_lora:
        positive_parts.append(f"<lora:{include_lora}:{lora_weight}>")

    # Assemble positive prompt
    positive_prompt = ", ".join(positive_parts)

    # Negative prompt
    if use_anything:
        negative_parts = NEGATIVE_TAGS_ANYTHING
    else:
        negative_parts = NEGATIVE_TAGS_NOVELAI

    negative_prompt = ", ".join(negative_parts)

    return positive_prompt, negative_prompt


def format_for_comfyui(positive: str, negative: str) -> str:
    """
    Format output as ComfyUI-friendly format
    """
    return f"""
+================================================================+
|                    ComfyUI Prompts                              |
+================================================================+
| Positive Prompt:                                                |
|----------------------------------------------------------------|
| {positive[:75]}
| {positive[75:150] if len(positive) > 75 else ''}
| {positive[150:225] if len(positive) > 150 else ''}
+================================================================+
| Negative Prompt:                                                |
|----------------------------------------------------------------|
| {negative[:75]}
| {negative[75:150] if len(negative) > 75 else ''}
+================================================================+
"""


def main():
    if len(sys.argv) < 2:
        print("""
+================================================================+
|          ComfyUI Anime Prompt Generator v1.0                    |
+================================================================+
| Usage:                                                          |
|   python generate_prompt.py <description>                       |
|   python generate_prompt.py <description> --lora <name>         |
|   python generate_prompt.py <description> --anything            |
|                                                                  |
| Examples:                                                        |
|   python generate_prompt.py "blue hair girl, smile, twintails"  |
|   python generate_prompt.py "Hatsune Miku" --lora "miku"        |
|   python generate_prompt.py "red dress girl" --anything         |
+================================================================+
        """)
        sys.exit(1)

    # Parse arguments
    description = sys.argv[1]
    include_lora = None
    lora_weight = 0.7
    use_anything = False

    if "--lora" in sys.argv:
        idx = sys.argv.index("--lora")
        if len(sys.argv) > idx + 1:
            include_lora = sys.argv[idx + 1]
    if "--weight" in sys.argv:
        idx = sys.argv.index("--weight")
        if len(sys.argv) > idx + 1:
            lora_weight = float(sys.argv[idx + 1])
    if "--anything" in sys.argv:
        use_anything = True

    print(f"\nDescription: {description}")
    if include_lora:
        print(f"LoRA: {include_lora} (weight: {lora_weight})")

    positive, negative = generate_from_description(
        description,
        include_lora=include_lora,
        lora_weight=lora_weight,
        use_anything=use_anything
    )

    print(format_for_comfyui(positive, negative))

    print("""
Tips:
   1. Paste the positive prompt into the KSampler positive prompt input
   2. Paste the negative prompt into the KSampler negative prompt input
   3. LoRA weight recommendation: 0.5-0.8, lower to 0.3-0.5 if results are poor
   4. If using Anything series models, add --anything flag
    """)


if __name__ == "__main__":
    main()
