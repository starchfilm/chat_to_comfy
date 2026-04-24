#!/usr/bin/env python3
"""
Civitai LoRA Search Script
Search for character LoRA on Civitai, returning download links, trigger words, recommended weights, etc.
No API Key required, uses Civitai public API directly

Note: The Civitai REST API may return 403/400 in some environments.
      If you encounter this, use web_search as a fallback (as described in SKILL.md).
"""

import urllib.request
import urllib.parse
import json
import sys
from typing import Optional


def search_civitai_lora(
    query: str,
    model_type: str = "Lora",
    base_url: str = "https://civitai.com/api/v1/models",
    limit: int = 5
) -> list[dict]:
    """
    Search for LoRA models on Civitai

    Args:
        query: Search keyword (character name, Chinese/English/Japanese/romaji all work)
        model_type: Model type, default Lora
        base_url: API endpoint
        limit: Number of results to return

    Returns:
        List of dictionaries containing LoRA information
    """
    params = {
        "types": model_type,
        "query": query,
        "limit": limit,
        "sort": "Downloads"  # Sort by downloads
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("items", [])
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP {e.code}: Civitai API may be blocked in your environment.")
        print(f"        Try using web_search with keywords like '{query} LoRA civitai' instead.")
        return []
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return []


def format_lora_result(item: dict) -> str:
    """
    Format a single LoRA result as a readable string
    """
    name = item.get("name", "N/A")
    model_id = item.get("id", "N/A")
    version = item.get("modelVersions", [{}])[0] if item.get("modelVersions") else {}
    version_name = version.get("name", "N/A")

    # Download URL from first available version
    files = version.get("files", [])
    download_url = "N/A"
    if files:
        download_url = files[0].get("downloadUrl", "N/A")

    # Trigger words
    trigger_words = version.get("trainedWords", [])
    trigger_str = ", ".join(trigger_words[:10]) if trigger_words else "No specific trigger words"

    # Statistics
    stats = item.get("stats", {})
    downloads = stats.get("downloadCount", 0)
    rating = stats.get("rating", 0.0)

    # Recommended weight (based on community consensus)
    base_model = version.get("baseModel", "N/A")

    result = f"""
========================================
LoRA: {name}
----------------------------------------
Version: {version_name}
Download: {download_url}
Downloads: {downloads:,}
Rating: {rating:.1f}/5.0
Base Model: {base_model}

Trigger Words:
   {trigger_str}

Recommended Usage:
   - LoRA weight: 0.5 - 0.8 (character resemblance)
   - Sampling steps: 20-30
   - CFG: 7-9
========================================"""
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python search_lora.py <character_name>")
        print("Examples: python search_lora.py Hatsune Miku")
        print("          python search_lora.py Raiden Shogun")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"\nSearching Civitai LoRA: {query}\n")

    results = search_civitai_lora(query, limit=5)

    if not results:
        print("No LoRA found. Try:")
        print("   1. Use the character's official English name")
        print("   2. Use romaji spelling")
        print("   3. Add 'anime' or 'character' keyword")
        sys.exit(0)

    print(f"Found {len(results)} results:\n")

    for i, item in enumerate(results, 1):
        print(f"[{i}] {format_lora_result(item)}")

    print(f"\nTip: For full trigger word lists and weight recommendations, check the LoRA detail page")
    print(f"   After downloading, test with low weight (0.3-0.5) first, then adjust based on results")


if __name__ == "__main__":
    main()
