"""
Repo2Brainrot Video Generation Pipeline

Takes episode scripts (JSON) and produces final videos with:
- TTS audio (Kokoro — 82M param local model, high quality)
- Word-level subtitles (wav2vec2 forced alignment → .ass)
- Background gameplay video from assets/
- Code snippet overlays (Pillow, reads REAL code from repo)
- TikTok-style HTML player for the feed

Usage:
    python skills/repo2brainrot/scripts/generate_video.py --scripts output/my-repo/scripts/ --assets assets/ --output output/my-repo/videos/ --repo repos/my-repo
"""

import argparse
import json
import math
import os
import random
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio
from kokoro import KPipeline
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUBTITLE_STYLE = (
    "Style: Default,Impact,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
    "-1,0,0,0,100,100,0,0,1,3,1,5,10,10,40,1"
)

KOKORO_VOICE = "af_heart"   # clear, natural female voice
KOKORO_SPEED = 1.3          # fast but still understandable
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280          # 9:16 vertical (720p — good enough for mobile, much smaller files)
VIDEO_CRF = 28               # libx264 quality — 23=high quality large, 28=good quality small
MAX_EPISODE_SECONDS = 60     # hard cap — split into parts if longer

# Code overlay config — BIGGER font for readability
CODE_FONT_SIZE = 30
CODE_LINE_HEIGHT = CODE_FONT_SIZE + 10
CODE_BG_COLOR = (30, 30, 46, 240)   # #1E1E2E – Catppuccin Mocha base
CODE_TEXT_COLOR = (205, 214, 244)    # #CDD6F4
CODE_KEYWORD_COLOR = (137, 180, 250) # #89B4FA
CODE_STRING_COLOR = (166, 227, 161)  # #A6E3A1
CODE_COMMENT_COLOR = (108, 112, 134) # #6C7086
CODE_PADDING = 32
CODE_MAX_LINES = 12                  # truncate long snippets

# Initialize Kokoro pipeline once (model loads on first use)
_kokoro_pipeline = None


def get_kokoro_pipeline():
    global _kokoro_pipeline
    if _kokoro_pipeline is None:
        print("  Loading Kokoro TTS model...")
        _kokoro_pipeline = KPipeline(lang_code="a")  # American English
    return _kokoro_pipeline


# ---------------------------------------------------------------------------
# Step 1: TTS Audio Generation (Kokoro)
# ---------------------------------------------------------------------------

def generate_tts(
    text: str,
    output_path: str,
    voice: str = KOKORO_VOICE,
    speed: float = KOKORO_SPEED,
) -> str:
    """Convert text to speech using Kokoro and save as WAV.

    Returns path to the 16kHz WAV (for forced alignment).
    """
    pipeline = get_kokoro_pipeline()
    audio_segments = []
    generator = pipeline(text, voice=voice, speed=speed)
    for _i, (_gs, _ps, audio) in enumerate(generator):
        audio_segments.append(audio)

    if not audio_segments:
        raise RuntimeError("Kokoro produced no audio output")

    full_audio = np.concatenate(audio_segments)

    # Save high-quality 24kHz version (for final video)
    hq_path = output_path.replace(".wav", "_24k.wav")
    sf.write(hq_path, full_audio, 24000)

    # Convert to 16kHz mono for forced alignment
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", hq_path,
            "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
            output_path,
        ],
        check=True,
        capture_output=True,
    )
    print(f"  ✓ TTS audio: {output_path}")
    return hq_path


# ---------------------------------------------------------------------------
# Step 2: Forced Alignment → ASS Subtitles (wav2vec2)
# ---------------------------------------------------------------------------

def forced_align(audio_path: str, transcript: str) -> list[tuple[str, float, float]]:
    """Use wav2vec2 for word-level timestamps.

    Returns list of (word, start_sec, end_sec).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model().to(device)
    labels = bundle.get_labels()
    dictionary = {c: i for i, c in enumerate(labels)}

    waveform, sr = torchaudio.load(audio_path)
    if sr != bundle.sample_rate:
        waveform = torchaudio.functional.resample(waveform, sr, bundle.sample_rate)

    with torch.inference_mode():
        emissions, _ = model(waveform.to(device))
        emissions = torch.log_softmax(emissions, dim=-1)
    emission = emissions[0].cpu().detach()

    # Clean transcript for alignment
    clean = transcript.upper()
    clean = re.sub(r"[^A-Z '\n]", "", clean)
    words = clean.split()
    if not words:
        return []

    token_str = "|" + "|".join(words) + "|"
    tokens = [dictionary.get(c, 0) for c in token_str]

    # Build trellis
    num_frame = emission.size(0)
    num_tokens = len(tokens)
    if num_tokens > num_frame:
        # Transcript too long for audio — return even spacing
        return _even_spacing(transcript, waveform.size(1) / bundle.sample_rate)

    trellis = torch.zeros((num_frame, num_tokens))
    trellis[1:, 0] = torch.cumsum(emission[1:, 0], 0)
    trellis[0, 1:] = -float("inf")
    safe_start = max(0, num_frame - num_tokens + 1)
    trellis[safe_start:, 0] = float("inf")

    for t in range(num_frame - 1):
        trellis[t + 1, 1:] = torch.maximum(
            trellis[t, 1:] + emission[t, 0],
            trellis[t, :-1] + emission[t, tokens[1:]],
        )

    # Backtrack
    t, j = num_frame - 1, num_tokens - 1
    path = [(j, t)]
    while j > 0 and t > 0:
        p_stay = trellis[t - 1, j]
        p_change = trellis[t - 1, j - 1] if j > 0 else torch.tensor(-float("inf"))
        t -= 1
        if p_change > p_stay and j > 0:
            j -= 1
        path.append((j, t))
    path = path[::-1]

    # Merge into character segments
    segments = []
    i1 = 0
    while i1 < len(path):
        i2 = i1
        while i2 < len(path) and path[i1][0] == path[i2][0]:
            i2 += 1
        idx = path[i1][0]
        char = token_str[idx] if idx < len(token_str) else "|"
        segments.append((char, path[i1][1], path[i2 - 1][1]))
        i1 = i2

    # Merge characters into words
    ratio = waveform.size(1) / num_frame
    sample_rate = bundle.sample_rate
    word_timings = []
    current_word = ""
    word_start = None

    for char, start_frame, end_frame in segments:
        if char == "|":
            if current_word:
                word_timings.append((
                    current_word,
                    (word_start * ratio) / sample_rate,
                    (end_frame * ratio) / sample_rate,
                ))
                current_word = ""
                word_start = None
        else:
            if word_start is None:
                word_start = start_frame
            current_word += char

    if current_word and word_start is not None:
        word_timings.append((
            current_word,
            (word_start * ratio) / sample_rate,
            (segments[-1][2] * ratio) / sample_rate,
        ))

    # Map back to original mixed-case words
    original_words = transcript.split()
    result = []
    for i, (_, start, end) in enumerate(word_timings):
        word = original_words[i] if i < len(original_words) else _
        result.append((word, start, end))
    return result


def _even_spacing(transcript: str, duration: float) -> list[tuple[str, float, float]]:
    """Fallback: evenly space words across duration."""
    words = transcript.split()
    if not words:
        return []
    dt = duration / len(words)
    return [(w, i * dt, (i + 1) * dt) for i, w in enumerate(words)]


def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def generate_ass_subtitles(
    word_timings: list[tuple[str, float, float]],
    output_path: str,
) -> None:
    header = f"""[Script Info]
Title: Repo2Brainrot Subtitles
ScriptType: v4.00+
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{SUBTITLE_STYLE}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for word, start, end in word_timings:
        s = format_ass_time(start)
        e = format_ass_time(end)
        # Escape ASS special chars
        safe_word = word.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        events.append(f"Dialogue: 0,{s},{e},Default,,0,0,0,,{safe_word}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(events))
        f.write("\n")
    print(f"  ✓ Subtitles: {output_path}")


# ---------------------------------------------------------------------------
# Step 3: Code Snippet Image — reads REAL code from the repo
# ---------------------------------------------------------------------------

def read_code_from_repo(repo_path: str, file_path: str, lines: str = "") -> str:
    """Read actual code from the repo. ``lines`` can be '5-15' or empty for whole file."""
    full_path = os.path.join(repo_path, file_path)
    if not os.path.isfile(full_path):
        return f"// File not found: {file_path}"

    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    if lines and "-" in lines:
        parts = lines.split("-")
        start = max(0, int(parts[0]) - 1)
        end = min(len(all_lines), int(parts[1]))
        selected = all_lines[start:end]
    else:
        selected = all_lines[:CODE_MAX_LINES]

    # Truncate to max lines
    if len(selected) > CODE_MAX_LINES:
        selected = selected[:CODE_MAX_LINES]
        selected.append("  // ...\n")

    return "".join(selected).rstrip()


def render_code_image(
    code: str,
    output_path: str,
    caption: str = "",
    width: int = int(VIDEO_WIDTH * 0.9),
) -> None:
    """Render a code snippet as a PNG with dark background and large font."""
    lines = code.split("\n")
    if len(lines) > CODE_MAX_LINES:
        lines = lines[:CODE_MAX_LINES] + ["  // ..."]

    # Load monospace font
    font = _load_mono_font(CODE_FONT_SIZE)
    caption_font = _load_mono_font(CODE_FONT_SIZE - 4)

    height = CODE_PADDING * 2 + CODE_LINE_HEIGHT * len(lines)
    if caption:
        height += CODE_LINE_HEIGHT + 8

    img = Image.new("RGBA", (width, height), CODE_BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Rounded border
    draw.rounded_rectangle(
        [(0, 0), (width - 1, height - 1)],
        radius=16,
        outline=(80, 80, 100, 255),
        width=2,
    )

    # Fake window dots (macOS style)
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse(
            [(CODE_PADDING + i * 22, 12), (CODE_PADDING + i * 22 + 14, 26)],
            fill=(*color, 255),
        )

    # Draw code lines
    y = CODE_PADDING + 20  # below dots
    for line in lines:
        x = CODE_PADDING
        _draw_highlighted_line(draw, x, y, line, font)
        y += CODE_LINE_HEIGHT

    # Caption
    if caption:
        y += 8
        draw.text((CODE_PADDING, y), caption, fill=(180, 190, 220, 255), font=caption_font)

    img.save(output_path, "PNG")
    print(f"  ✓ Code image: {output_path}")


def _load_mono_font(size: int):
    """Try multiple monospace fonts, fall back to default."""
    for name in ["consola.ttf", "CascadiaCode.ttf", "JetBrainsMono-Regular.ttf",
                  "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    # Try system paths on Windows
    winfonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    for name in ["consola.ttf", "cour.ttf", "lucon.ttf"]:
        try:
            return ImageFont.truetype(os.path.join(winfonts, name), size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_highlighted_line(draw, x, y, line, font):
    """Draw a single line with basic syntax highlighting."""
    keywords = {
        "import", "from", "export", "default", "const", "let", "var",
        "function", "return", "if", "else", "class", "def", "async",
        "await", "new", "this", "self", "true", "false", "null", "None",
        "require", "module", "extends", "super", "yield", "for", "while",
    }

    stripped = line.strip()
    if stripped.startswith(("//", "#", "/*", "*", "<!--")):
        draw.text((x, y), line, fill=CODE_COMMENT_COLOR, font=font)
        return

    # Tokenize and color
    tokens = re.split(r"(\b\w+\b|\"[^\"]*\"|'[^']*'|`[^`]*`)", line)
    cx = x
    for token in tokens:
        if not token:
            continue
        if token.lower() in keywords:
            color = CODE_KEYWORD_COLOR
        elif token.startswith(('"', "'", "`")):
            color = CODE_STRING_COLOR
        else:
            color = CODE_TEXT_COLOR
        draw.text((cx, y), token, fill=color, font=font)
        bbox = font.getbbox(token)
        cx += (bbox[2] - bbox[0]) if bbox else len(token) * CODE_FONT_SIZE // 2


# ---------------------------------------------------------------------------
# Step 4: Video Assembly (FFmpeg)
# ---------------------------------------------------------------------------

def find_word_time(word_timings: list[tuple], highlight: str) -> float | None:
    """Return the start timestamp (seconds) of the first word matching highlight.

    Tries exact match first, then substring match so 'createStore' finds
    a token like 'createstore' in the alignment output.
    """
    if not highlight or not word_timings:
        return None
    target = highlight.lower()
    # exact match pass
    for word, start, _end in word_timings:
        if word.lower() == target:
            return start
    # substring match pass
    for word, start, _end in word_timings:
        if target in word.lower() or word.lower() in target:
            return start
    return None


def pick_background_video(assets_dir: str) -> str:
    videos = [f for f in os.listdir(assets_dir) if f.endswith(".mp4")]
    if not videos:
        raise FileNotFoundError(f"No .mp4 files in {assets_dir}")
    return os.path.join(assets_dir, random.choice(videos))


def get_audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def assemble_video(
    background_video: str,
    audio_path: str,
    subtitle_path: str,
    code_images: list[dict],
    output_path: str,
) -> None:
    """Assemble final video: bg + audio + .ass subs + code overlays."""
    duration = get_audio_duration(audio_path)
    filters = []

    # Scale/crop bg to 9:16, dim
    filters.append(
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"eq=brightness=-0.12[bg]"
    )

    # ASS subtitles overlay
    sub_escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
    filters.append(f"[bg]ass='{sub_escaped}'[subbed]")
    last_stream = "subbed"

    input_args = ["-stream_loop", "-1", "-i", background_video, "-i", audio_path]
    input_idx = 2

    for i, ci in enumerate(code_images):
        if not os.path.exists(ci["path"]):
            continue
        input_args.extend(["-i", ci["path"]])
        show_at = ci.get("show_at_second", 0)
        dur = ci.get("duration", 5)

        img_y = int(VIDEO_HEIGHT * 0.58)
        img_x = f"(main_w-overlay_w)/2"  # centered

        new_stream = f"v{i}"
        filters.append(
            f"[{last_stream}][{input_idx}:v]overlay="
            f"x={img_x}:y={img_y}:"
            f"enable='between(t,{show_at},{show_at + dur})'[{new_stream}]"
        )
        last_stream = new_stream
        input_idx += 1

    filter_complex = ";".join(filters)

    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", filter_complex,
        "-map", f"[{last_stream}]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", str(VIDEO_CRF),
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        output_path,
    ]
    print(f"  ⚙ Assembling video...")
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  ✓ Video: {output_path}")


# ---------------------------------------------------------------------------
# Step 5: Episode Splitting (>60s → Part 1, Part 2, etc.)
# ---------------------------------------------------------------------------

def estimate_duration(narration: str, speed: float = KOKORO_SPEED) -> float:
    """Estimate TTS duration from word count. ~170 WPM at speed 1.1."""
    words = len(narration.split())
    wpm = 150 * speed  # Kokoro base ~150 WPM, scaled by speed
    return (words / wpm) * 60


def split_narration(narration: str, max_seconds: int = MAX_EPISODE_SECONDS) -> list[str]:
    """Split narration into parts that fit under max_seconds each."""
    est = estimate_duration(narration)
    if est <= max_seconds:
        return [narration]

    num_parts = math.ceil(est / max_seconds)
    sentences = re.split(r'(?<=[.!?])\s+', narration)

    parts = []
    current = []
    current_words = 0
    words_per_part = len(narration.split()) // num_parts

    for sentence in sentences:
        sw = len(sentence.split())
        if current_words + sw > words_per_part * 1.15 and current:
            parts.append(" ".join(current))
            current = [sentence]
            current_words = sw
        else:
            current.append(sentence)
            current_words += sw

    if current:
        parts.append(" ".join(current))

    return parts


# ---------------------------------------------------------------------------
# Step 6: TikTok Player HTML Generation
# ---------------------------------------------------------------------------

def generate_tiktok_player(episodes: list[dict], output_path: str) -> None:
    """Stamp episode list into the static player template."""
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "player-template.html"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    video_items = ""
    for ep in episodes:
        part_label = f" · Part {ep['part']}" if ep.get("part") else ""
        video_items += (
            f'\n        <div class="video-item" data-category="{ep.get("category", "")}">'
            f'\n            <video src="videos/{ep["video_file"]}" playsinline preload="metadata" loop></video>'
            f'\n            <div class="overlay">'
            f'\n                <div class="badge">{ep.get("category", "").upper().replace("-", " ")}</div>'
            f'\n                <div class="title">{ep.get("title", "")}</div>'
            f'\n                <div class="meta">Ep {ep.get("episode", "?")}{part_label} · {ep.get("difficulty", "")}</div>'
            f'\n            </div>'
            f'\n            <div class="progress-bar"><div class="progress-fill"></div></div>'
            f'\n        </div>'
        )

    html = template.replace("<!-- EPISODES_PLACEHOLDER -->", video_items)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ TikTok player: {output_path}")


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def process_episode(
    script: dict,
    assets_dir: str,
    output_dir: str,
    repo_path: str = "",
) -> list[dict]:
    """Process a single episode script → one or more final videos (split if >60s).

    Returns list of episode metadata dicts for the player.
    """
    ep_num = script["episode"]
    category = script.get("category", "unknown")
    title = script.get("title", f"Episode {ep_num}")
    narration = script["narration"]

    print(f"\n{'='*60}")
    print(f"Episode {ep_num}: {title}")
    print(f"Category: {category}")
    print(f"{'='*60}")

    # Split if narration is too long
    parts = split_narration(narration)
    num_parts = len(parts)
    if num_parts > 1:
        print(f"  ⚠ Narration too long — splitting into {num_parts} parts")

    audio_dir = os.path.join(output_dir, "..", "audio")
    subs_dir = os.path.join(output_dir, "..", "subs")
    code_dir = os.path.join(output_dir, "..", "code_images")
    for d in [output_dir, audio_dir, subs_dir, code_dir]:
        os.makedirs(d, exist_ok=True)

    results = []

    for part_idx, part_text in enumerate(parts):
        part_label = f"_pt{part_idx + 1}" if num_parts > 1 else ""
        part_title = f"{title} (Part {part_idx + 1})" if num_parts > 1 else title

        audio_path = os.path.join(audio_dir, f"ep{ep_num:02d}{part_label}.wav")
        sub_path = os.path.join(subs_dir, f"ep{ep_num:02d}{part_label}.ass")
        video_path = os.path.join(output_dir, f"ep{ep_num:02d}{part_label}.mp4")

        # Step 1: TTS
        print(f"  [1/4] Generating TTS audio{' (Part ' + str(part_idx+1) + ')' if num_parts > 1 else ''}...")
        hq_audio = generate_tts(part_text, audio_path)

        # Step 2: Forced alignment
        print(f"  [2/4] Running forced alignment...")
        word_timings = forced_align(audio_path, part_text)
        generate_ass_subtitles(word_timings, sub_path)

        # Step 3: Render code images (read REAL code from repo)
        print(f"  [3/4] Rendering code overlays...")
        code_images = []
        # Only attach code snippets to the first part (or proportionally)
        snippets = script.get("code_snippets", [])
        if num_parts > 1:
            chunk = len(snippets) // num_parts
            start = part_idx * max(chunk, 1)
            end = start + max(chunk, 1)
            snippets = snippets[start:end]

        for i, snippet in enumerate(snippets):
            img_path = os.path.join(code_dir, f"ep{ep_num:02d}{part_label}_code{i}.png")

            # Read REAL code from repo if available
            if repo_path and snippet.get("file"):
                code = read_code_from_repo(
                    repo_path,
                    snippet["file"],
                    snippet.get("lines", ""),
                )
            else:
                code = snippet.get("code", "// no code provided")

            render_code_image(
                code=code,
                output_path=img_path,
                caption=snippet.get("caption", ""),
            )
            code_images.append({
                "path": img_path,
                "show_at_second": snippet.get("show_at_second", 0),
                "duration": snippet.get("duration", 5),
                "highlight": snippet.get("highlight", ""),
            })

        # Auto-adjust overlay timing using forced-alignment word timestamps.
        for ci in code_images:
            t = find_word_time(word_timings, ci.get("highlight", ""))
            if t is not None:
                ci["show_at_second"] = max(0.0, t - 0.3)

        # Step 4: Assemble video
        print(f"  [4/4] Assembling final video...")
        bg_video = pick_background_video(assets_dir)
        assemble_video(
            background_video=bg_video,
            audio_path=hq_audio,  # use 24kHz version for better quality
            subtitle_path=sub_path,
            code_images=code_images,
            output_path=video_path,
        )

        results.append({
            "episode": ep_num,
            "part": part_idx + 1 if num_parts > 1 else None,
            "category": category,
            "title": part_title,
            "difficulty": script.get("difficulty", ""),
            "video_file": os.path.basename(video_path),
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Repo2Brainrot Video Pipeline")
    parser.add_argument("--scripts", required=True, help="Dir containing episode script JSONs")
    parser.add_argument("--assets", required=True, help="Dir containing background .mp4 videos")
    parser.add_argument("--output", required=True, help="Output dir for final videos")
    parser.add_argument("--repo", default="", help="Path to the original repo (for reading real code)")
    parser.add_argument("--episode", type=int, help="Generate only this episode number")
    args = parser.parse_args()

    script_files = sorted(Path(args.scripts).glob("*.json"))
    if not script_files:
        print(f"No script .json files found in {args.scripts}")
        sys.exit(1)

    print(f"Found {len(script_files)} episode scripts")
    print(f"Assets: {args.assets}")
    print(f"Repo: {args.repo or '(none — code from scripts)'}")
    print(f"Output: {args.output}")

    all_episodes = []
    for sf_path in script_files:
        with open(sf_path, "r", encoding="utf-8") as f:
            script = json.load(f)

        if args.episode and script.get("episode") != args.episode:
            continue

        results = process_episode(script, args.assets, args.output, repo_path=args.repo)
        all_episodes.extend(results)

    # Generate concat file for full feed
    os.makedirs(args.output, exist_ok=True)
    if len(all_episodes) > 1:
        concat_path = os.path.join(args.output, "filelist.txt")
        with open(concat_path, "w") as f:
            for ep in all_episodes:
                f.write(f"file '{ep['video_file']}'\n")
        full_path = os.path.join(args.output, "full_feed.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", concat_path, "-c", "copy", full_path],
            check=True, capture_output=True,
        )
        print(f"\n✓ Full feed: {full_path}")

    # Generate TikTok player HTML
    player_path = os.path.join(args.output, "..", "player.html")
    generate_tiktok_player(all_episodes, player_path)

    print(f"\n{'='*60}")
    print(f"Done! Generated {len(all_episodes)} videos.")
    print(f"Open player.html in a browser to watch the feed.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
