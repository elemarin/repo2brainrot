---
name: repo2brainrot
description: 'Analyze any code repository and generate TikTok-style doom-scroll video scripts. Use when: user wants to learn a codebase, generate brainrot videos, create tutorial content, analyze repo architecture, or says "repo2brainrot", "brainrot", "doom scroll", "tutorial videos", "explain this repo". Covers: auth, routing, state, components, API, styling, data models, CRUD, error handling, testing, build config, dependencies, project structure, forms, security, performance.'
argument-hint: 'Path to the repo folder to analyze (e.g., repos/my-app)'
---

# Repo2Brainrot — Turn Any Repo Into a Doom-Scroll Video Feed

Analyze a codebase across 16 universal categories, generate brainrot-style scripts, then produce actual short-form videos with TTS audio, word-level subtitles, code overlays, and background gameplay footage.

## When to Use

- User wants to understand a new codebase via short-form video
- User says "brainrot", "doom scroll", "explain this repo", "tutorial feed"
- User wants TikTok/Reels-style educational content from code
- User points at a repo and wants video breakdowns

## Pipeline Overview

```
Repo ──► Analysis ──► Episode Picker ──► Scripts ──► TTS ──► Alignment ──► Video ──► Player
  │        (16          (user picks     (<60s each,  (Kokoro   (wav2vec2    (FFmpeg)  (HTML
  │      categories)     categories)     parts if    82M,       → .ass              TikTok
  │                                      longer)    local)     subs)                feed)
  └── assets/1.mp4, 2.mp4, 3.mp4 (background footage) ─────────────────────────────────►
```

## Procedure

### Phase 1: Repo Deep Scan

Systematically analyze the repo across all 16 universal categories.

1. **Read the category definitions** from [./references/categories.md](./references/categories.md)
2. For each category, identify:
   - Key files involved (with line references)
   - Libraries/patterns used
   - How it connects to other categories
   - Complexity level (beginner / intermediate / advanced)
3. Score each category 0-3:
   - `0` = Not present (skip)
   - `1` = Minimal implementation
   - `2` = Standard implementation worth explaining
   - `3` = Complex / novel — prioritize these
4. Save the analysis as structured data in session memory

### Phase 1.5: Episode Picker

**Before generating anything, present the user with a category menu:**

1. Show the scored categories as a table:
   ```
   Which categories do you want videos for?

   | # | Category           | Score | Episodes | Est. Time |
   |---|-------------------|-------|----------|-----------|
   | 1 | Project Structure  | ★★☆   | 1        | ~0:45     |
   | 2 | State Management   | ★★★   | 3        | ~2:15     |
   | 3 | Authentication     | ★★★   | 2        | ~1:30     |
   ...

   Enter numbers (e.g., 1,2,3) or 'all' for everything:
   ```
2. Wait for user selection before proceeding
3. Only generate scripts for selected categories
4. This saves time — a full repo might generate 15+ episodes

### Phase 2: Script Generation

Generate video scripts following the brainrot format.

1. **Read the video format spec** from [./references/video-format.md](./references/video-format.md)
2. **Read the analysis procedure** from [./references/analysis-procedure.md](./references/analysis-procedure.md)
3. Generate scripts per category in priority order (score 3 first, then 2, then 1)
4. Each category gets 1-3 episodes based on score
5. **Hard cap: 60 seconds per episode.** If a topic needs more time, split into Part 1, Part 2, etc.
6. Scripts should read like reddit story brainrot — fast, punchy, no filler
7. Write all scripts to `output/<repo-name>/scripts/` as individual `.json` files:

```json
{
  "episode": 1,
  "category": "state-management",
  "title": "This App Has 8 Brains and They All Share One Body",
  "difficulty": "intermediate",
  "duration_target_seconds": 45,
  "narration": "Okay so this app uses Redux right...",
  "code_snippets": [
    {
      "file": "src/store.js",
      "lines": "1-15",
      "highlight": "createStore",
      "show_at_second": 8,
      "duration": 5
    }
  ],
  "visual_cues": [
    {"at_second": 0, "text": "🧠 STATE MANAGEMENT", "position": "top-center"},
    {"at_second": 5, "text": "8 reducers = 8 brain slices", "position": "bottom"}
  ]
}
```

### Phase 3: Video Generation

For each episode script, produce a video. Run the generation pipeline:

1. **Check prerequisites** — Ensure Python dependencies are installed:
   ```
   pip install -r .github/skills/repo2brainrot/scripts/requirements.txt
   ```
2. **Generate all videos** by running the pipeline script:
   ```
   python .github/skills/repo2brainrot/scripts/generate_video.py --scripts output/<repo-name>/scripts/ --assets assets/ --output output/<repo-name>/videos/
   ```

The pipeline does the following per episode:

#### Step 3a: TTS Audio Generation (Kokoro)
- Uses [Kokoro](https://github.com/hexgrad/kokoro) — 82M param open-weight TTS model
- Apache licensed, runs locally, no API key needed
- Way better voice quality than edge-tts — natural, expressive, fast
- Speed set to 1.1x for brainrot pacing
- Requires `espeak-ng` installed on system (Windows: download MSI from espeak-ng releases)
- Voice: `af_heart` (clear, natural)
- Output: `output/<repo-name>/audio/ep{N}.wav` (24kHz) + 16kHz version for alignment

#### Step 3b: Forced Alignment (Subtitle Generation)
- Uses `wav2vec2` (via torchaudio) to align audio with transcript
- Produces word-level timestamps
- Converts to `.ass` subtitle format — Impact 48pt, white with black outline, center-screen
- Falls back to even-spaced timing if alignment fails
- Output: `output/<repo-name>/subs/ep{N}.ass`

#### Step 3c: Code Overlays (Pillow)
- Reads **REAL code** from the actual repo files (not copy-pasted into scripts)
- Font size: 26pt monospace (Consolas/Cascadia/JetBrains Mono) — readable on mobile
- Dark background (#1E1E2E) with macOS-style window dots, rounded corners
- Catppuccin syntax highlighting (keywords blue, strings green, comments gray)
- Max 12 lines per snippet — choose punchy sections
- Centered on bottom third of screen

#### Step 3d: Video Assembly (FFmpeg)
- Picks a random background video from `assets/` (1.mp4, 2.mp4, 3.mp4)
- Loops background to match audio duration
- Overlays: .ass subtitles + code images
- Composites everything with FFmpeg (libx264, CRF 23)
- Output: `output/<repo-name>/videos/ep{N}.mp4`

#### Step 3e: Auto-Split
- If narration exceeds 60 seconds, pipeline automatically splits into parts
- Each part becomes its own video (ep01_pt1.mp4, ep01_pt2.mp4)
- Code snippets distributed proportionally across parts

### Phase 4: Feed Assembly

1. Create a `feed.md` manifest in `output/<repo-name>/`:

```markdown
# 🧠 [Repo Name] — Brainrot Tutorial Feed
> [X] episodes across [Y] categories | Total watch time: ~[Z] minutes

## Episode List
| # | Title | Category | Duration | File |
|---|-------|----------|----------|------|
| 1 | This App Has 8 Brains... | State | 0:45 | videos/ep1.mp4 |
```

2. Order for engagement:
   - Start with Project Structure (orientation)
   - Alternate heavy/light categories
   - End with Build/Config (satisfying closure)

3. Optionally generate a concatenated full video

### Phase 5: TikTok Player

Generate a self-contained HTML file that mimics TikTok's vertical video feed:

- **Vertical scroll-snap** — swipe/scroll between episodes
- **Auto-play** — video plays when scrolled into view, pauses when scrolled away
- **Tap to pause** — click/tap the video to pause/resume
- **Progress bar** — thin bar at bottom shows playback position
- **Episode counter** — "3 / 12" fixed at top
- **Category badges** — glassmorphic badge on each video
- **Keyboard nav** — arrow keys to navigate, space to pause
- **Dark theme** — pure black, designed for the content

The player is generated automatically at `output/<repo-name>/player.html`.
Open it in any browser to watch the feed.

## Output Structure

```
output/<repo-name>/
├── feed.md              # Episode manifest
├── analysis.json        # Raw category analysis
├── scripts/             # Episode scripts (JSON)
│   ├── ep01_state.json
│   ├── ep02_auth.json
│   └── ...
├── audio/               # TTS audio (WAV)
│   ├── ep01.wav
│   └── ...
├── subs/                # Forced-aligned subtitles (ASS)
│   ├── ep01.ass
│   └── ...
├── videos/              # Final videos (MP4)
│   ├── ep01.mp4
│   ├── ep01_pt2.mp4     # Part 2 if episode was split
│   ├── ep02.mp4
│   └── full_feed.mp4    # Optional concatenated feed
└── player.html          # TikTok-style HTML player
```

## Key Principles

- **Hook or die** — First 3 seconds must grab attention with a wild claim or question
- **One concept per episode** — Never mix categories
- **Show the code** — Every claim references a real file and line
- **Gen-Z energy** — Fast pace, memes, analogies to gaming/social media
- **Accuracy first** — Brainrot style but technically correct
- **Progressive difficulty** — Start simple, build across the feed
- **Real background footage** — Use the gameplay/satisfying videos from assets/
