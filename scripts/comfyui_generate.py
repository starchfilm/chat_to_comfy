"""
ComfyUI Image Generation Script (Cross-Platform)
Standard anime generation workflow with multi-LoRA chaining, HiRes fix, and workflow export.

Usage (CLI):
  python comfyui_generate.py --help
  python comfyui_generate.py --positive "1girl, solo, ..." --lora "your_lora.safetensors"
  python comfyui_generate.py --positive "..." --lora "LoRA1" --lora "LoRA2" --save-workflow

Usage (called by AI assistant):
  AI constructs parameters and calls this script directly

Configuration:
  Copy config.example.json to config.json in the same directory to customize defaults.
  Environment variables COMFYUI_URL, COMFYUI_OUTPUT_DIR, WORKSPACE_DIR also supported.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import platform

# === Configuration loading ===
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)
_CONFIG_PATH = os.path.join(_SKILL_DIR, "config.json")

# Default values (overridden by config.json if present)
_DEFAULTS = {
    "comfyui_url": "http://127.0.0.1:8188",
    "comfyui_output_dir": "",
    "default_checkpoint": "your_model.safetensors",
    "default_lora": "your_style_lora.safetensors",
    "default_lora_strength_model": 1.0,
    "default_lora_strength_clip": 1.0,
    "default_style_artists": "your, artist, tags, here",
    "default_quality_tags": "masterpiece, best quality, amazing quality,",
    "default_negative_embeddings": "embedding:badhandv4, embedding:easynegative",
    "default_negative_prompt": "furry, bad anatomy, low quality, lowres, normal quality, worst quality, bad proportions, out of focus, extra arms, extra limb, missing fingers, too many fingers, bad feet, bad hands, mutated hands, poorly drawn hands, malformed hands, mutated hands and fingers, logo, english text, chibi, multi character, watermark",
    "default_width": 896,
    "default_height": 1152,
    "default_steps": 30,
    "default_cfg": 7.0,
    "default_sampler": "euler",
    "default_scheduler": "normal",
    "hires_fix": True,
    "hires_steps": 10,
    "hires_cfg": 7.5,
    "hires_denoise": 0.3,
    "hires_width": 1472,
    "hires_height": 1856,
    "upscale_model": "RealESRGAN_x4plus_anime_6B.pth",
}


def _load_config():
    """Load config.json if available, merge with defaults."""
    config = _DEFAULTS.copy()
    if os.path.isfile(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            config.update(user_config)
            print(f"Loaded config from {_CONFIG_PATH}")
        except Exception as e:
            print(f"WARNING: Failed to load config.json: {e}")
    return config


CONFIG = _load_config()

COMFYUI_URL = os.environ.get("COMFYUI_URL", CONFIG["comfyui_url"])
COMFYUI_OUTPUT_DIR = os.environ.get("COMFYUI_OUTPUT_DIR", CONFIG["comfyui_output_dir"])
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", os.getcwd())

_IS_WINDOWS = platform.system() == "Windows"


def _detect_output_dir():
    """Auto-detect ComfyUI output directory (cross-platform)."""
    if COMFYUI_OUTPUT_DIR and os.path.isdir(COMFYUI_OUTPUT_DIR):
        return COMFYUI_OUTPUT_DIR

    # Try to infer from running ComfyUI process
    try:
        import subprocess
        if _IS_WINDOWS:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe", "/V", "/FO", "CSV"],
                capture_output=True, text=True, timeout=5
            )
        else:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=5
            )
        for line in result.stdout.splitlines():
            line = line.strip()
            if "comfyui" in line.lower() or "main.py" in line.lower():
                for part in line.split():
                    if part.endswith("main.py") or part.endswith("main.py\""):
                        comfy_root = os.path.dirname(part.strip('"'))
                        candidate = os.path.join(comfy_root, "output")
                        if os.path.isdir(candidate):
                            return candidate
    except Exception:
        pass

    # Search common paths
    if _IS_WINDOWS:
        search_roots = []
        for drive in ["E:", "D:", "C:"]:
            for root_dir in [r"\comfy", r"\ComfyUI", r"\AI\comfy"]:
                search_roots.append(drive + root_dir)
        sub_candidates = [
            r"ComfyUI\output",
            r"ComfyUI_Max\ComfyUI\output",
            r"output",
        ]
    else:
        search_roots = [
            os.path.expanduser("~/comfy"),
            os.path.expanduser("~/ComfyUI"),
            os.path.expanduser("~/AI/comfy"),
            "/opt/comfy",
            "/opt/ComfyUI",
        ]
        sub_candidates = [
            "ComfyUI/output",
            "output",
        ]

    for root in search_roots:
        for sub in sub_candidates:
            candidate = os.path.join(root, sub)
            if os.path.isdir(candidate):
                return candidate

    return ""


def api_get(path, timeout=10):
    """GET request to ComfyUI API."""
    req = urllib.request.Request(f"{COMFYUI_URL}{path}")
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read())


def api_post(path, data, timeout=15):
    """POST request to ComfyUI API."""
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}{path}",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read())


def check_comfyui():
    """Check if ComfyUI is online."""
    try:
        api_get("/system_stats", timeout=5)
        return True
    except Exception:
        return False


def list_checkpoints():
    """Get available checkpoint list."""
    try:
        d = api_get("/object_info/CheckpointLoaderSimple")
        return d["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    except Exception:
        return []


def list_loras():
    """Get available LoRA list."""
    try:
        d = api_get("/object_info/LoraLoader")
        return d["LoraLoader"]["input"]["required"]["lora_name"][0]
    except Exception:
        return []


def build_workflow(
    checkpoint=None,
    loras=None,
    positive_prompt="",
    negative_prompt="",
    width=None,
    height=None,
    seed=-1,
    steps=None,
    cfg=None,
    sampler=None,
    scheduler=None,
    hires_fix=None,
    hires_steps=None,
    hires_cfg=None,
    hires_denoise=None,
    hires_width=None,
    hires_height=None,
    upscale_model=None,
    filename_prefix="ComfyUI",
    style_artists=None,
    quality_tags=None,
    negative_embeddings=None,
):
    """
    Build workflow dict based on standard anime generation template.
    
    LoRA chaining structure:
      Checkpoint → LoRA #1 (style/detail) → LoRA #2 (character) → [LoRA #3 (optional)] → CLIP/KSampler
    
    loras parameter format:
      [
        {"name": "xxx.safetensors", "strength_model": 1.0, "strength_clip": 1.0},
        {"name": "yyy.safetensors", "strength_model": 0.8, "strength_clip": 0.8},
      ]
    """
    # Apply config defaults
    if checkpoint is None:
        checkpoint = CONFIG["default_checkpoint"]
    if width is None:
        width = CONFIG["default_width"]
    if height is None:
        height = CONFIG["default_height"]
    if steps is None:
        steps = CONFIG["default_steps"]
    if cfg is None:
        cfg = CONFIG["default_cfg"]
    if sampler is None:
        sampler = CONFIG["default_sampler"]
    if scheduler is None:
        scheduler = CONFIG["default_scheduler"]
    if hires_fix is None:
        hires_fix = CONFIG["hires_fix"]
    if hires_steps is None:
        hires_steps = CONFIG["hires_steps"]
    if hires_cfg is None:
        hires_cfg = CONFIG["hires_cfg"]
    if hires_denoise is None:
        hires_denoise = CONFIG["hires_denoise"]
    if hires_width is None:
        hires_width = CONFIG["hires_width"]
    if hires_height is None:
        hires_height = CONFIG["hires_height"]
    if upscale_model is None:
        upscale_model = CONFIG["upscale_model"]
    if style_artists is None:
        style_artists = CONFIG["default_style_artists"]
    if quality_tags is None:
        quality_tags = CONFIG["default_quality_tags"]
    if negative_embeddings is None:
        negative_embeddings = CONFIG["default_negative_embeddings"]

    if loras is None:
        loras = [
            {
                "name": CONFIG["default_lora"],
                "strength_model": CONFIG["default_lora_strength_model"],
                "strength_clip": CONFIG["default_lora_strength_clip"],
            },
        ]

    # Default negative prompt
    if not negative_prompt:
        negative_prompt = (
            CONFIG["default_negative_prompt"]
            + ", "
            + negative_embeddings
        )

    # Assemble positive prompt
    full_positive = f"{style_artists},\n{quality_tags}\n{positive_prompt}"

    # Seed handling
    if seed == -1:
        seed = int(time.time() * 1000) % (2**53)

    # === Build nodes ===
    workflow = {}

    # [1] Checkpoint
    workflow["1"] = {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": checkpoint}
    }

    # LoRA chaining
    prev_model = ["1", 0]
    prev_clip = ["1", 1]

    lora_node_ids = ["30", "33", "21"]  # Reuse template node IDs
    for i, lora_cfg in enumerate(loras):
        if i >= 3:
            break  # Max 3 LoRAs
        node_id = lora_node_ids[i]
        workflow[node_id] = {
            "class_type": "LoraLoader",
            "inputs": {
                "model": prev_model,
                "clip": prev_clip,
                "lora_name": lora_cfg["name"],
                "strength_model": lora_cfg.get("strength_model", 1.0),
                "strength_clip": lora_cfg.get("strength_clip", 1.0),
            }
        }
        prev_model = [node_id, 0]
        prev_clip = [node_id, 1]

    final_model = prev_model
    final_clip = prev_clip

    # [3] Positive prompt
    workflow["3"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"clip": final_clip, "text": full_positive}
    }

    # [4] Negative prompt
    workflow["4"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"clip": final_clip, "text": negative_prompt}
    }

    # [6] EmptyLatentImage
    workflow["6"] = {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": width, "height": height, "batch_size": 1}
    }

    # [5] KSampler #1 — Main generation
    workflow["5"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": final_model,
            "positive": ["3", 0],
            "negative": ["4", 0],
            "latent_image": ["6", 0],
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler,
            "scheduler": scheduler,
            "denoise": 1.0,
        }
    }

    # [10] VAEDecodeTiled — Main generation decode
    workflow["10"] = {
        "class_type": "VAEDecodeTiled",
        "inputs": {
            "samples": ["5", 0],
            "vae": ["1", 2],
            "tile_size": 512,
            "overlap": 64,
            "temporal_size": 64,
            "temporal_overlap": 8,
        }
    }

    # [18] PreviewImage — Preview (main generation result)
    workflow["18"] = {
        "class_type": "PreviewImage",
        "inputs": {"images": ["10", 0]}
    }

    if hires_fix:
        # [11] UpscaleModelLoader
        workflow["11"] = {
            "class_type": "UpscaleModelLoader",
            "inputs": {"model_name": upscale_model}
        }

        # [12] ImageUpscaleWithModel
        workflow["12"] = {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {
                "upscale_model": ["11", 0],
                "image": ["10", 0],
            }
        }

        # [13] ImageScale
        workflow["13"] = {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["12", 0],
                "upscale_method": "nearest-exact",
                "width": hires_width,
                "height": hires_height,
                "crop": "disabled",
            }
        }

        # [14] VAEEncodeTiled
        workflow["14"] = {
            "class_type": "VAEEncodeTiled",
            "inputs": {
                "pixels": ["13", 0],
                "vae": ["1", 2],
                "tile_size": 512,
                "overlap": 64,
                "temporal_size": 64,
                "temporal_overlap": 8,
            }
        }

        # [15] KSampler #2 — HiRes fix
        workflow["15"] = {
            "class_type": "KSampler",
            "inputs": {
                "model": final_model,
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["14", 0],
                "seed": seed,
                "steps": hires_steps,
                "cfg": hires_cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": hires_denoise,
            }
        }

        # [7] VAEDecode — HiRes fix decode
        workflow["7"] = {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["15", 0],
                "vae": ["1", 2],
            }
        }

        # [9] SaveImage
        workflow["9"] = {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": filename_prefix}
        }
    else:
        # No HiRes fix, save main generation result directly
        workflow["9"] = {
            "class_type": "SaveImage",
            "inputs": {"images": ["10", 0], "filename_prefix": filename_prefix}
        }

    return workflow


def submit_and_wait(workflow, max_wait=300, poll_interval=5):
    """Submit workflow and wait for completion, returning output file info."""
    payload = {"prompt": workflow}
    result = api_post("/prompt", payload)
    prompt_id = result.get("prompt_id")

    if not prompt_id:
        return {"error": "No prompt_id returned", "detail": result}

    node_errors = result.get("node_errors", {})
    if node_errors:
        return {"error": "Node errors", "detail": node_errors}

    print(f"Submitted: prompt_id={prompt_id}")

    # Poll for completion
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        try:
            history = api_get(f"/history/{prompt_id}")
        except Exception:
            continue

        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {}).get("status_str", "")

            if status == "success":
                outputs = entry.get("outputs", {})
                images = []
                for node_id, node_out in outputs.items():
                    if "images" in node_out:
                        for img in node_out["images"]:
                            images.append({
                                "filename": img["filename"],
                                "subfolder": img.get("subfolder", ""),
                                "type": img.get("type", "output"),
                            })
                return {"status": "success", "images": images, "prompt_id": prompt_id}

            elif status == "error":
                return {"error": "Execution failed", "detail": entry.get("status", {})}

        print(f"  Waiting... ({elapsed}s)")

    return {"error": "Timeout", "detail": f"Waited {max_wait}s without completion"}


def copy_to_workspace(images, filename_prefix="", output_dir=None):
    """Copy output images to workspace comfyui-output/ subdirectory."""
    if output_dir is None:
        output_dir = _detect_output_dir()
    if not output_dir:
        print("WARNING: Cannot detect ComfyUI output directory. Set COMFYUI_OUTPUT_DIR env var or comfyui_output_dir in config.json.")
        return []

    # All outputs go to comfyui-output/ subdirectory, not workspace root
    dest_dir = os.path.join(WORKSPACE_DIR, "comfyui-output")
    os.makedirs(dest_dir, exist_ok=True)

    copied = []
    for img in images:
        if img["type"] == "temp":
            continue  # Skip temp preview images
        src = os.path.join(output_dir, img["subfolder"], img["filename"])
        dst = os.path.join(dest_dir, img["filename"])
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dst)
            copied.append(dst)
            print(f"Copied: {dst}")
        else:
            print(f"WARNING: File not found: {src}")
    return copied


def save_workflow_json(workflow, filepath):
    """Save workflow as ComfyUI-loadable JSON file (to comfyui-output/ subdirectory)."""
    dir_path = os.path.dirname(filepath)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    # ComfyUI Load API format
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"Workflow saved: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="ComfyUI Anime Image Generation Script")

    # === Checkpoint ===
    parser.add_argument("--checkpoint", default=None,
                        help=f"Checkpoint name (default: {CONFIG['default_checkpoint']})")
    parser.add_argument("--list-checkpoints", action="store_true",
                        help="List available checkpoints and exit")

    # === LoRA ===
    parser.add_argument("--lora", action="append", nargs="+",
                        help="LoRA: name [model_strength] [clip_strength], can specify multiple times, e.g. --lora NAME 0.8 0.8")
    parser.add_argument("--list-loras", action="store_true",
                        help="List available LoRAs and exit")

    # === Prompts ===
    parser.add_argument("--positive", "-p", required=False, default="",
                        help="Positive prompt")
    parser.add_argument("--negative", "-n", default="",
                        help="Negative prompt (leave empty for default)")
    parser.add_argument("--style-artists", default=None,
                        help="Artist style tags (leave empty for default from config)")
    parser.add_argument("--quality-tags", default=None,
                        help="Quality tags (leave empty for default from config)")

    # === Resolution / Sampling ===
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--seed", type=int, default=-1, help="-1=random")
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--cfg", type=float, default=None)
    parser.add_argument("--sampler", default=None)
    parser.add_argument("--scheduler", default=None)

    # === HiRes fix ===
    parser.add_argument("--no-hires", action="store_true",
                        help="Disable HiRes fix")
    parser.add_argument("--hires-steps", type=int, default=None)
    parser.add_argument("--hires-cfg", type=float, default=None)
    parser.add_argument("--hires-denoise", type=float, default=None)
    parser.add_argument("--hires-width", type=int, default=None)
    parser.add_argument("--hires-height", type=int, default=None)
    parser.add_argument("--upscale-model", default=None)

    # === Output ===
    parser.add_argument("--filename-prefix", default="ComfyUI")
    parser.add_argument("--save-workflow", action="store_true",
                        help="Save workflow JSON to {workspace}/comfyui-output/ (can import in ComfyUI via Load API for manual fine-tuning)")
    parser.add_argument("--copy-to-workspace", action="store_true",
                        help="Copy output images to {workspace}/comfyui-output/")

    # === ComfyUI Status ===
    parser.add_argument("--check-status", action="store_true",
                        help="Check if ComfyUI is online")

    args = parser.parse_args()

    # === Quick commands ===
    if args.check_status:
        if check_comfyui():
            print("ComfyUI is ONLINE")
        else:
            print("ComfyUI is OFFLINE - Please start ComfyUI first")
        return

    if args.list_checkpoints:
        for ckpt in list_checkpoints():
            print(ckpt)
        return

    if args.list_loras:
        for lora in list_loras():
            print(lora)
        return

    # === Check online ===
    if not check_comfyui():
        print(f"ERROR: ComfyUI is not running at {COMFYUI_URL}")
        print("Please start ComfyUI first, then retry.")
        sys.exit(1)

    # === Parse LoRA ===
    loras = []
    if args.lora:
        for lora_spec in args.lora:
            name = lora_spec[0]
            sm = float(lora_spec[1]) if len(lora_spec) > 1 else CONFIG["default_lora_strength_model"]
            sc = float(lora_spec[2]) if len(lora_spec) > 2 else sm
            loras.append({"name": name, "strength_model": sm, "strength_clip": sc})
    
    # Default LoRA (if none specified)
    if not loras:
        loras = [
            {
                "name": CONFIG["default_lora"],
                "strength_model": CONFIG["default_lora_strength_model"],
                "strength_clip": CONFIG["default_lora_strength_clip"],
            },
        ]

    # === Build workflow ===
    workflow = build_workflow(
        checkpoint=args.checkpoint,
        loras=loras,
        positive_prompt=args.positive,
        negative_prompt=args.negative,
        width=args.width,
        height=args.height,
        seed=args.seed,
        steps=args.steps,
        cfg=args.cfg,
        sampler=args.sampler,
        scheduler=args.scheduler,
        hires_fix=not args.no_hires,
        hires_steps=args.hires_steps,
        hires_cfg=args.hires_cfg,
        hires_denoise=args.hires_denoise,
        hires_width=args.hires_width,
        hires_height=args.hires_height,
        upscale_model=args.upscale_model,
        filename_prefix=args.filename_prefix,
        style_artists=args.style_artists,
        quality_tags=args.quality_tags,
    )

    # === Save workflow ===
    if args.save_workflow:
        dest_dir = os.path.join(WORKSPACE_DIR, "comfyui-output")
        os.makedirs(dest_dir, exist_ok=True)
        save_path = os.path.join(dest_dir, f"{args.filename_prefix}_workflow.json")
        save_workflow_json(workflow, save_path)

    # === Submit ===
    ckpt_name = args.checkpoint or CONFIG["default_checkpoint"]
    hires_on = not args.no_hires and CONFIG["hires_fix"]
    print(f"Submitting workflow...")
    print(f"  Checkpoint: {ckpt_name}")
    print(f"  LoRAs: {json.dumps(loras, ensure_ascii=False)}")
    print(f"  Resolution: {args.width or CONFIG['default_width']}x{args.height or CONFIG['default_height']}")
    print(f"  Hires fix: {'OFF' if not hires_on else 'ON'}")
    print(f"  Steps: {args.steps or CONFIG['default_steps']} + {'0' if not hires_on else (args.hires_steps or CONFIG['hires_steps'])}")

    result = submit_and_wait(workflow)

    if "error" in result:
        print(f"ERROR: {result['error']}")
        print(f"Detail: {result.get('detail', '')}")
        sys.exit(1)

    print(f"\nGeneration successful!")
    print(f"Prompt ID: {result['prompt_id']}")

    for img in result["images"]:
        if img["type"] == "output":
            output_dir = _detect_output_dir()
            if output_dir:
                full_path = os.path.join(output_dir, img["subfolder"], img["filename"])
            else:
                full_path = img["filename"]
            print(f"Output: {full_path}")

    # === Copy to workspace ===
    if args.copy_to_workspace:
        copied = copy_to_workspace(result["images"], args.filename_prefix)
        if copied:
            print(f"\nCopied to workspace:")
            for p in copied:
                print(f"  {p}")

    # Output JSON for AI parsing
    output = {
        "status": "success",
        "prompt_id": result["prompt_id"],
        "images": [img for img in result["images"] if img["type"] == "output"],
    }
    print(f"\n__JSON_OUTPUT__{json.dumps(output, ensure_ascii=False)}__JSON_OUTPUT__")


if __name__ == "__main__":
    main()
