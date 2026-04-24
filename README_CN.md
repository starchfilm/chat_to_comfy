# Chat to Comfy

[English](README.md) | 中文

一个 AI 驱动的二次元图像生成技能包，适配 [WorkBuddy](https://www.codebuddy.cn/)（或任何 OpenClaw 兼容的 AI 编程助手）。搜参考图、找 LoRA、写提示词、ComfyUI API 出图——全部自然语言搞定。

> **运行原理**：这不是一个独立应用，而是一个**技能包**，教 AI Agent 如何帮你做二次元出图。Agent 读取 `SKILL.md` 知道何时触发、怎么执行，然后调用 `scripts/` 里的 Python 脚本与本地 ComfyUI 交互。你需要一个支持 skill 系统的 AI 助手（目前是 WorkBuddy / CodeBuddy）+ 本地运行的 ComfyUI 实例。

## 功能

- **找参考图** — 搜索 Pixiv 镜像站和动漫 Wiki，找角色参考图
- **找 LoRA** — 搜索 Civitai / RunningHub / LibLib，返回触发词和推荐权重
- **写提示词** — 分层模板系统（静态层/动态层分离），高效迭代
- **角色情报** — 查询热门角色和官方外观设定
- **ComfyUI 出图** — 通过 REST API 提交工作流，支持高清修复、多 LoRA 串联、工作流 JSON 导出

## 前置条件

| 功能 | 需要联网 | 需要本地 ComfyUI |
|------|:---:|:---:|
| 找参考图 | 是 | 否 |
| 找 LoRA | 是 | 否 |
| 写提示词 | 否 | 否 |
| 角色情报 | 是 | 否 |
| ComfyUI 出图 | 否 | **是** |
| 打开 ComfyUI 界面 | 否 | **是** |

没有 ComfyUI 也能用前 4 项功能。出图需要本地运行 ComfyUI（`http://127.0.0.1:8188`）。

## 安装

### 方式一：安装为 WorkBuddy Skill

将整个目录复制到 WorkBuddy skills 文件夹：

```bash
# 用户级 skill（所有项目可用）
cp -r chat_to_comfy/ ~/.workbuddy/skills/anime-aigc-workflow/

# 或项目级 skill（团队共享）
cp -r chat_to_comfy/ .workbuddy/skills/anime-aigc-workflow/
```

### 方式二：独立使用脚本

`scripts/` 中的脚本可以独立运行：

```bash
# 通过 ComfyUI API 生图
python scripts/comfyui_generate.py --positive "1girl, solo, ..." --lora "your_lora.safetensors" 0.8 0.8

# 在 Civitai 搜索 LoRA
python scripts/search_lora.py "Hatsune Miku"

# 生成分层提示词
python scripts/generate_prompt.py "蓝发少女, 微笑, 双马尾, 室内"
```

## 配置

将 `config.example.json` 复制为 `config.json` 并自定义：

```json
{
  "comfyui_url": "http://127.0.0.1:8188",
  "default_checkpoint": "你的模型.safetensors",
  "default_lora": "你的画风LoRA.safetensors",
  "default_style_artists": "你的, 画师, tag",
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

也可以通过环境变量配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `COMFYUI_URL` | ComfyUI API 地址 | `http://127.0.0.1:8188` |
| `COMFYUI_OUTPUT_DIR` | ComfyUI 输出目录（留空自动检测） | *(自动)* |
| `WORKSPACE_DIR` | 工作区根目录 | 当前目录 |

## 使用方式（WorkBuddy Skill）

安装后，直接用自然语言跟 AI 助手说：

| 你说 | 触发功能 |
|------|---------|
| "找初音未来的参考图" | 参考图搜索 |
| "找雷电将军的 LoRA" | LoRA 搜索 |
| "写一个蓝发校服少女的提示词" | 提示词生成 |
| "最近什么角色火？" | 角色情报 |
| "帮我出一张初音未来的图" / "跑图" | ComfyUI 生图 |
| "打开 ComfyUI" / "我要手动调" | 打开 ComfyUI 界面 |

## 提示词分层系统

提示词模板将**静态层**（很少变化）和**动态层**（每张图不同）分离，迭代更高效：

```
[A. 质量]           ← 固定：masterpiece, best quality, ...
[B. LoRA + 角色]    ← 角色固定：触发词 + 官方外观
[C. 服装]           ← 动态：每张图可换
[D. 表情]           ← 动态：每张图可换
[E. 动作/姿势]      ← 动态：每张图可换
[F. 场景/光效]      ← 动态：每张图可换
[G. 负向提示词]     ← 固定：质量过滤
```

完整模板和 tag 参考见 `references/anime_prompt_guide.md`。

## ComfyUI 工作流拓扑

```
Checkpoint → LoRA #1 (画风) → LoRA #2 (角色) → [LoRA #3 (可选)]
    → CLIP Text Encode (正向/负向)
    → KSampler #1 (主生成)
    → Tiled VAE Decode (8GB 显存友好)
    → ESRGAN 超分
    → ImageScale
    → Tiled VAE Encode
    → KSampler #2 (高清修复)
    → VAE Decode → Save Image
```

核心特性：
- **Tiled VAE**（tile 512, overlap 64）— 8GB 显存可跑
- **多 LoRA 串联** — 最多 3 个 LoRA 串联
- **高清修复** — ESRGAN 4x 超分 + 二次采样
- **工作流导出** — 保存 JSON，可在 ComfyUI 中 "Load API" 手动微调

## 项目结构

```
chat_to_comfy/
├── SKILL.md                      # Skill 定义（触发词 + 执行指令）
├── README.md                     # English README
├── README_CN.md                  # 中文说明（本文件）
├── LICENSE                       # MIT 许可证
├── config.example.json           # 配置模板
├── assets/
│   └── workflow_template.json    # ComfyUI 工作流模板参考
├── references/
│   ├── anime_prompt_guide.md     # Tag 写作指南 + 分层模板
│   ├── civitai_api.md            # Civitai API 文档 + 搜索策略
│   └── workflow_guide.md         # ComfyUI 工作流操作手册
└── scripts/
    ├── comfyui_generate.py       # ComfyUI API 提交脚本
    ├── generate_prompt.py         # 提示词生成器（中文→英文 tag 映射）
    └── search_lora.py             # Civitai LoRA 搜索脚本
```

## 核心原则

1. **中文角色名 → 官方英文名** 是找到 LoRA 的关键。搜索时务必使用角色官方英文名或罗马音。
2. **写提示词前先确认外观**。永远不要猜发色、瞳色或配饰——先搜索官方设定。
3. **只搜索不抓取**。在 AI 助手环境中，`web_fetch` 访问复杂页面（Wiki、Civitai 等）经常超时。用 `web_search` 多换几个关键词更靠谱。

## 参与贡献

欢迎贡献！随时提交 Pull Request。特别欢迎以下方向：

- 更多 LoRA 来源集成
- 跨平台 ComfyUI 路径检测改进
- 更多角色名查询表
- WebUI (Automatic1111/Forge) API 支持

## 许可证

[MIT](LICENSE)
