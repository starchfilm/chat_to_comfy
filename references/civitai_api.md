# Civitai API Reference Documentation

## Overview

Civitai provides a public REST API that requires no API Key. Suitable for individual users to automate LoRA/model searches.

**Important**: The Civitai REST API may return 403/400 in some environments. If you encounter this, use `web_search` with multiple keyword variations as a fallback (see SKILL.md for the search strategy).

## Basic Information

- **Base URL**: `https://civitai.com/api/v1/`
- **Authentication**: None required (public endpoint)
- **Rate Limiting**: Add appropriate delays between requests to avoid throttling

## Core Endpoints

### 1. Search Models (models)

**Endpoint**: `GET /api/v1/models`

**Query Parameters**:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `query` | string | Search keyword | `Hatsune Miku` |
| `types` | string | Model type | `Lora`, `Checkpoint`, `TextualInversion` |
| `sort` | string | Sort order | `Downloads`, `Newest`, `Highest Rated` |
| `limit` | int | Return count (max 100) | `10` |
| `page` | int | Page number | `1` |
| `tag` | string | Tag filter | `anime` |

**Request Example**:

```bash
# Search LoRA
curl "https://civitai.com/api/v1/models?types=Lora&query=Miku&limit=5"

# Sort by downloads
curl "https://civitai.com/api/v1/models?types=Lora&query=girl&sort=Downloads"
```

**Response Fields**:

```json
{
  "items": [
    {
      "id": 12345,
      "name": "Miku",
      "description": "Vocaloid character...",
      "type": "Lora",
      "modelVersions": [
        {
          "id": 111,
          "name": "v1.0",
          "baseModel": "SD 1.5",
          "trainedWords": ["miku", "hatsune", "vocaloid"],
          "files": [
            {
              "name": "miku.safetensors",
              "downloadUrl": "https://civitai.com/api/download/models/..."
            }
          ]
        }
      ],
      "stats": {
        "downloadCount": 50000,
        "rating": 4.8,
        "favoriteCount": 1200
      }
    }
  ]
}
```

### 2. Get Model Details

**Endpoint**: `GET /api/v1/models/{id}`

```bash
curl "https://civitai.com/api/v1/models/12345"
```

### 3. Get Model Images

**Endpoint**: `GET /api/v1/models/{id}/images`

```bash
curl "https://civitai.com/api/v1/models/12345/images?limit=6"
```

## Character Name Lookup Table

**Important**: When searching Civitai/RunningHub, you must use the official English name. Chinese names rarely produce results.

Here are some commonly searched characters as examples. Add your own to this table as you discover them:

| Character (Chinese) | Official English Name | Recommended Search Keywords |
|---------------------|----------------------|---------------------------|
| 初音未来 | Hatsune Miku | `Hatsune Miku`, `Miku Vocaloid` |
| 雷电将军 | Raiden Shogun | `Raiden Shogun`, `Raiden Shogun Genshin` |
| 刻晴 | Keqing | `Keqing`, `Keqing Genshin` |
| 八重神子 | Yae Miko | `Yae Miko`, `Yae Miko Genshin` |
| 流萤 | Firefly | `Firefly`, `Firefly HSR` |
| 银狼 | Silver Wolf | `Silver Wolf`, `Silver Wolf HSR` |
| 知更鸟 | Robin | `Robin HSR`, `Robin Honkai` |

> **Pattern**: For miHoYo/HoYoverse game characters, append the game abbreviation (HSR for Honkai: Star Rail, Genshin for Genshin Impact) to the English name for better results.

## Search Strategies

### Character Name Search Tips

| Search Scenario | Keyword Strategy |
|----------------|-----------------|
| Japanese character | Use romaji, e.g. `Hatsune Miku` instead of `初音ミク` |
| Chinese character | Translate to English, e.g. `Keqing` instead of `刻晴` |
| Game character | Add game name, e.g. `Eula genshin` |
| miHoYo character | Add game abbreviation (Genshin Impact: `Genshin`, Honkai: Star Rail: `HSR`) |

### How to Filter the Best LoRA

1. **Download count**: Downloads > 5,000 usually indicate stable quality (> 10,000 preferred)
2. **Rating**: Rating > 4.5/5 preferred
3. **Base model**: Confirm the LoRA's base model is compatible with your main model
   - SD 1.5 models: Broadest compatibility
   - SDXL models: Require SDXL-specific LoRA
   - Illustrious/Pony models: Require corresponding LoRA
4. **Trigger words**: Check `trainedWords` for clean, concise triggers

### LoRA Download Sites (No VPN Required in China)

| Site | Purpose | URL |
|------|---------|-----|
| RunningHub | LoRA downloads (China) | runninghub.cn |
| TensorHub | Model mirror | tensorhub.art |
| CivArchive | Civitai mirror | civarchive.com |
| LibLib | LoRA downloads | liblib.art |

## Python Example

```python
import requests

def search_lora(query: str, limit: int = 5):
    url = "https://civitai.com/api/v1/models"
    params = {
        "types": "Lora",
        "query": query,
        "sort": "Downloads",
        "limit": limit
    }
    response = requests.get(url, params=params)
    return response.json()
```

## Important Notes

1. **Respect copyright**: LoRA is for personal learning use only; commercial use requires proper licensing
2. **Version compatibility**: SD 1.5 and SDXL LoRAs are not interchangeable
3. **Download speed**: Civitai servers are faster during off-peak hours
4. **Caching**: Cache search results locally to reduce repeated requests
5. **API availability**: The Civitai API may be blocked in certain environments. Always have a `web_search` fallback strategy
