# repo2brainrot

Turn a code repository into a TikTok-style doom-scroll video feed.

Point it at a repo, pick the most interesting parts, and turn the codebase into short-form episodes with narration, subtitles, code overlays, and a swipeable feed.

It works with **GitHub Copilot CLI**, **GitHub Copilot in VS Code / agent mode**, **Claude Code**, and other tools that support the open **Agent Skills** format.

## What it produces

```text
output/<repo-name>/
├── player.html
├── videos/ep01.mp4
├── videos/full_feed.mp4
├── scripts/
├── audio/
├── subs/
└── analysis.json
```

Each episode includes:

- AI narration with Kokoro TTS
- Word-level subtitles
- Syntax-highlighted code overlays from the real repo
- Vertical background footage
- Auto-splitting when a topic runs past 60 seconds

## Use it with Copilot CLI

Install the whole repository as a plugin:

```bash
copilot plugin install OWNER/REPO
```

Then use the skill in a Copilot CLI session:

```text
/repo2brainrot repos/my-repo
```

## Use it as a standalone skill

If you want to use the skill outside the plugin flow, copy `skills/repo2brainrot/` into one of these supported skill locations:

- Copilot personal skills: `~/.copilot/skills/repo2brainrot/`
- Claude personal skills: `~/.claude/skills/repo2brainrot/`
- Generic Agent Skills location: `~/.agents/skills/repo2brainrot/`

Or add it as a project skill inside a target repository:

- Copilot project skill: `.github/skills/repo2brainrot/`
- Claude project skill: `.claude/skills/repo2brainrot/`
- Generic project skill: `.agents/skills/repo2brainrot/`

The important part is the folder shape: one skill directory containing `SKILL.md` and its bundled resources.

## Prerequisites

### System dependencies

```bash
# ffmpeg (required for video assembly)
winget install Gyan.FFmpeg

# espeak-ng (required for Kokoro phonemizer)
# Windows: install from https://github.com/espeak-ng/espeak-ng/releases
```

### Python dependencies

From a clone of this repository:

```bash
pip install -r skills/repo2brainrot/scripts/requirements.txt
```

Requires Python 3.11+ and enough disk space for PyTorch and the Kokoro model download.

## Quick start

### 1. Add gameplay footage

Put 1-3 background clips in `assets/`.

### 2. Add a repo to analyze

```bash
git clone https://github.com/some/repo repos/my-repo
```

### 3. Run the skill

```text
/repo2brainrot repos/my-repo
```

Copilot will analyze the repo, ask which categories you want, write scripts, generate videos, and build `player.html`.

## Run the video pipeline manually

If you already have episode JSON files and want to render them directly from this repository:

```bash
python skills/repo2brainrot/scripts/generate_video.py \
  --scripts output/my-repo/scripts/ \
  --assets assets/ \
  --output output/my-repo/videos/ \
  --repo repos/my-repo
```

To serve the generated feed:

```bash
cd output/my-repo
python -m http.server 8888
```

Then open `http://localhost:8888/player.html`.

## Repo layout

```text
repo2brainrot/
├── plugin.json
├── README.md
├── .gitignore
├── skills/
│   └── repo2brainrot/
│       ├── SKILL.md
│       ├── player-template.html
│       ├── references/
│       │   ├── categories.md
│       │   ├── video-format.md
│       │   └── analysis-procedure.md
│       └── scripts/
│           ├── generate_video.py
│           ├── compress_videos.py
│           └── requirements.txt
├── assets/
├── repos/
└── output/
```

## Tech stack

- Skill orchestration: Agent Skills + GitHub Copilot CLI
- TTS: Kokoro 82M
- Subtitle alignment: wav2vec2 via torchaudio
- Code rendering: Pillow
- Video assembly: FFmpeg

## Demo

![repo2brainrot demo](assets/demo.gif)

## License

MIT
