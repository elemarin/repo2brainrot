# 🧠 repo2brainrot

**Turn any GitHub repo into a TikTok-style doom-scroll video feed.**

Powered by a [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli) skill — Copilot analyzes your codebase across 16 categories, writes brainrot-style scripts, and generates actual short-form videos with AI voice, word-level subtitles, syntax-highlighted code overlays, and background gameplay footage.

[![demo](https://img.shields.io/badge/watch-demo_feed-ff0050?style=for-the-badge&logo=tiktok)](output/)

---

## What it produces

```
output/<repo-name>/
├── player.html          ← TikTok-style scroll feed. Open in browser.
├── videos/ep01.mp4      ← Individual episodes (~45-60s each)
├── videos/full_feed.mp4 ← All episodes concatenated
├── scripts/             ← Episode JSON scripts (editable)
├── audio/               ← Kokoro TTS WAV files
├── subs/                ← Word-level .ass subtitle files
└── analysis.json        ← Full 16-category repo analysis
```

Each episode:
- 🎙️ **AI narration** — Kokoro 82M TTS at 1.5x speed, reddit-story energy
- 📝 **Word-by-word subtitles** — wav2vec2 forced alignment, Impact font, center-screen
- 💻 **Code overlays** — reads real files from your repo, Catppuccin dark theme, 26pt
- 🎮 **Background footage** — Subway Surfers / Minecraft parkour vibes
- ⏱️ **Hard 60s cap** — auto-splits longer topics into Part 1, Part 2

---

## Quick Start

### 1. Prerequisites

**System dependencies:**
```bash
# ffmpeg (required for video assembly)
# Windows:
winget install Gyan.FFmpeg

# espeak-ng (required for Kokoro TTS phonemizer)
# Windows: download MSI from https://github.com/espeak-ng/espeak-ng/releases
```

**Python dependencies:**
```bash
pip install -r .github/skills/repo2brainrot/scripts/requirements.txt
```
> Requires Python 3.11+ and ~4GB disk for Torch + Kokoro model (downloads on first run)

**Background videos** — add 1-3 gameplay/satisfying clips to `assets/`:
```
assets/
├── 1.mp4   ← e.g. Subway Surfers, Minecraft parkour, satisfying clips
├── 2.mp4
└── 3.mp4
```
These are the background footage for your videos. Not included in this repo (too large) — source your own.

### 2. Add a repo to analyze

```bash
# Clone or copy the repo you want to analyze into repos/
git clone https://github.com/some/repo repos/my-repo
```

### 3. Run via GitHub Copilot CLI

```
/repo2brainrot repos/my-repo
```

Copilot will:
1. Scan the repo across 16 categories and score them
2. Show you a category menu — pick what you want
3. Write the episode scripts
4. Run the video pipeline
5. Serve `player.html` at `http://localhost:8888`

### 4. Or run manually

```bash
# Generate videos from pre-written scripts
python .github/skills/repo2brainrot/scripts/generate_video.py \
  --scripts output/my-repo/scripts/ \
  --assets assets/ \
  --output output/my-repo/videos/ \
  --repo repos/my-repo

# Serve the player
cd output/my-repo
python -m http.server 8888
# Open http://localhost:8888/player.html
```

---

## How It Works

```
Repo ──► Analysis ──► Episode Picker ──► Scripts ──► TTS ──► Alignment ──► Video ──► Player
  │        (16          (you choose)     (<60s,      Kokoro   wav2vec2    FFmpeg    HTML
  │      categories)                     auto-split)  82M     → .ass               TikTok
  └── assets/1.mp4, 2.mp4, 3.mp4 (background footage) ─────────────────────────────────►
```

### The 16 Categories

Every repo is analyzed across these dimensions (scored 0-3, higher = more interesting content):

| # | Category | What it covers |
|---|----------|---------------|
| 1 | 🗂️ Project Structure | Folder layout, entry points, naming conventions |
| 2 | 📦 Dependencies | Libraries, package manager, why they were chosen |
| 3 | 🔑 Authentication | JWT, OAuth, sessions, protected routes |
| 4 | 🗺️ Routing | URL mapping, navigation, route guards |
| 5 | 🧠 State Management | Redux, Zustand, Context, reducers, middleware |
| 6 | 🧩 Components/UI | Component hierarchy, patterns, hooks |
| 7 | 🌐 API Layer | HTTP clients, endpoints, data fetching |
| 8 | 🎨 Styling | CSS approach, design system, theming |
| 9 | 📐 Data Models | Types, interfaces, schemas, validation |
| 10 | 📝 Forms & Input | Controlled inputs, validation, submission |
| 11 | ✏️ CRUD | Create/Read/Update/Delete patterns |
| 12 | 🛡️ Error Handling | Error boundaries, display, recovery |
| 13 | 🧪 Testing | Unit/integration/e2e tests, coverage |
| 14 | ⚙️ Build & Config | Webpack/Vite, env vars, CI/CD |
| 15 | 🔒 Security | XSS, CSRF, sanitization, token safety |
| 16 | ⚡ Performance | Memoization, lazy loading, pagination, caching |

### Script Format

Scripts are plain JSON — fully editable before rendering:

```json
{
  "episode": 1,
  "category": "state-management",
  "title": "36 Action Types. ONE File. I'm Not Even Kidding.",
  "difficulty": "intermediate",
  "duration_target_seconds": 55,
  "narration": "So I open the constants folder right, and there's ONE file...",
  "code_snippets": [
    {
      "file": "src/constants/actionTypes.js",
      "lines": "1-10",
      "highlight": "APP_LOAD",
      "show_at_second": 8,
      "duration": 6,
      "caption": "^ every possible action, one file"
    }
  ],
  "visual_cues": [
    { "at_second": 0, "text": "🧠 STATE MANAGEMENT", "position": "top-center", "style": "badge" }
  ]
}
```

The `highlight` field is used to auto-sync the code overlay: the pipeline finds exactly when that word is spoken (via forced alignment) and shows the overlay 0.3s before it.

---

## Repo Structure

```
repo2brainrot/
├── README.md
├── .gitignore
├── .github/
│   └── skills/
│       └── repo2brainrot/
│           ├── SKILL.md           ← Copilot CLI skill definition
│           ├── references/
│           │   ├── categories.md  ← The 16 analysis categories
│           │   ├── video-format.md ← Script format spec
│           │   └── analysis-procedure.md ← How to analyze repos
│           └── scripts/
│               ├── generate_video.py  ← Full pipeline (TTS→Align→Overlay→FFmpeg)
│               └── requirements.txt
├── assets/                        ← Background videos (add your own, not in repo)
│   └── .gitkeep
├── repos/                         ← Clone repos here to analyze (not in repo)
│   └── .gitkeep
└── output/                        ← Generated videos and scripts (not in repo)
    └── .gitkeep
```

---

## Customization

### Change voice or speed
Edit `generate_video.py` constants:
```python
KOKORO_VOICE = "af_heart"   # or: am_michael, af_sarah, bf_emma, bm_george
KOKORO_SPEED = 1.5          # 1.0 = normal, 1.5 = brainrot pacing
```

### Change video resolution
```python
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920   # 9:16 vertical (TikTok/Reels/Shorts)
```

### Re-render a single episode
```bash
python .github/skills/repo2brainrot/scripts/generate_video.py \
  --scripts output/my-repo/scripts/ \
  --assets assets/ \
  --output output/my-repo/videos/ \
  --episode 3   # only render episode 3
```

---

## Tech Stack

| Component | Tech | Why |
|-----------|------|-----|
| TTS | [Kokoro 82M](https://github.com/hexgrad/kokoro) | Local, Apache licensed, great voice quality |
| Subtitle alignment | wav2vec2 (torchaudio) | Word-level timestamps, runs offline |
| Code rendering | Pillow | Syntax highlighting, Catppuccin theme |
| Video assembly | FFmpeg | Industry standard, handles everything |
| AI orchestration | GitHub Copilot CLI | Repo analysis + script writing |

---

## Requirements

- Python 3.11+
- ffmpeg on PATH
- espeak-ng installed
- ~4GB disk for PyTorch + Kokoro model (auto-downloads first run)
- Background `.mp4` files in `assets/`
- GPU optional (runs on CPU, just slower for TTS)

---

## License

MIT — use it, fork it, make your own brainrot.
