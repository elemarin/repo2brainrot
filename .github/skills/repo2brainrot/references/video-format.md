# Brainrot Video Script Format

Every episode follows this structure. Think reddit stories brainrot — those TikToks where someone reads a wild reddit post over Subway Surfers. Same energy, but for code.

The script needs to work as both a text document (for the LLM to generate) and as input to the video pipeline.

## HARD RULES

- **60 seconds MAX per video.** No exceptions. If the topic needs more time → Part 1, Part 2, Part 3.
- **~150 words max** per episode narration (at 1.1x speed = ~55 seconds).
- **No filler.** Every sentence must either hook, teach, or land. Cut anything that doesn't.
- **Read like a reddit post** — casual, first-person, like you're telling someone a story.

## The Hook-Explain-Payoff Structure

Every episode follows this arc (capped at 60 seconds):

### 1. HOOK (0-3 seconds)
Grab attention immediately. Think reddit title energy:
- **Wild claim:** "This app has 8 BRAINS and they all share ONE body"
- **Reddit-style:** "TIFU by reading this app's auth code and it's actually genius"
- **Shock stat:** "36 action types. ONE file. I'm not even kidding."
- **Challenge:** "I bet you can't guess where this app hides your password"
- **Pattern interrupt:** "STOP. This one file? Controls the entire app."
- **Storytime:** "So I was reading through this codebase and I found something insane..."

### 2. EXPLAIN (3-45 seconds)
The meat. Keep it TIGHT:
- **Analogy first** — Start with something they know. "Redux is basically a group chat where every component gets every message"
- **Show the code** — Actual code from the repo appears on screen. Point to the key lines.
- **One concept only** — Auth JWT and protected routes? Two separate videos.
- **Build tension** — "But here's the crazy part..."
- **Speed** — No pauses. Every second has content. Dead air = they scroll away.
- **Reddit storytelling** — "So basically what happens is..." / "And then I realized..." / "The wildest part?"

### 3. PAYOFF (45-60 seconds)
Land it FAST:
- **Mind-blown:** "Every. Single. API call. Gets your token. Automatically."
- **Callback:** "THAT's why it has 8 brains."
- **Cliffhanger:** "But we haven't talked about what happens when those brains DISAGREE... Part 2."
- **Takeaway:** "Next time you see Redux, you'll know exactly what's happening."

## Part Splitting Rules

When a topic needs more than 60 seconds:

1. **End Part 1 on a cliffhanger** — "But here's where it gets really interesting... Part 2."
2. **Part 2 starts with a 1-sentence recap** — "Remember those 8 reducers? Here's how they talk to each other."
3. **Each part is self-contained** — someone watching only Part 2 should still learn something.
4. **Max 3 parts per category** — if you need more, you're going too deep.

## Script JSON Schema

```json
{
  "episode": 1,
  "category": "state-management",
  "title": "This App Has 8 Brains and They All Share One Body",
  "difficulty": "intermediate",
  "duration_target_seconds": 55,
  "narration": "Write like a reddit post being read aloud. Casual, first-person, story-driven. Max 150 words. Use contractions. Use 'right?' and 'okay so' and 'basically' naturally. No formal language. Imagine you just found something insane in a codebase and you're telling your friend about it.",
  "code_snippets": [
    {
      "file": "src/store.js",
      "lines": "1-15",
      "code": "const store = createStore(\n  reducer,\n  applyMiddleware(...)\n);",
      "highlight": "createStore",
      "show_at_second": 8,
      "duration": 5,
      "caption": "^ this one line creates the entire brain"
    }
  ],
  "visual_cues": [
    {
      "at_second": 0,
      "text": "🧠 STATE MANAGEMENT",
      "position": "top-center",
      "style": "badge"
    },
    {
      "at_second": 15,
      "text": "auth → common → editor → home → articleList → article → profile → settings",
      "position": "bottom",
      "style": "list-reveal"
    }
  ]
}
```

## Narration Style Guide

### DO (reddit storytelling energy):
- "So I'm reading through this codebase right, and I find this ONE file that controls everything"
- "Basically every API call gets your JWT token automatically. You don't even DO anything."
- "Here's the thing nobody tells you about middleware..."
- "Watch. One import. That's it. That's the whole auth system."
- "I found 8 reducers in this app. EIGHT. Let me show you what they do."
- Short sentences. Punchy. Like you're texting.
- Use "basically", "literally", "wild", "insane" naturally
- Use "bro", "no cap" SPARINGLY (max 1 per episode)

### DON'T:
- "In this video, we will explore the authentication system" (too formal — instant scroll)
- "As you can see in the code below..." (too tutorial-y)
- "Let me explain how Redux works from the beginning" (too slow — cut to the point)
- Don't explain the programming language itself — assume they code
- Don't pad with filler — if you can cut a sentence, cut it

### Pacing Target:
- ~170 words per minute (Kokoro at 1.1x speed)
- Target: ~150 words per episode (~55 seconds)
- NEVER exceed 170 words (would blow past 60s)

## Subtitle Style (ASS Format)

Subtitles appear **word-by-word** in the center of the screen, TikTok/reddit-stories style:

```
[V4+ Styles]
Style: Default,Impact,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,5,10,10,40,1
```

Key style properties:
- **Font:** Impact (bold, high contrast)
- **Size:** 48pt (LARGE — readable on mobile, like the reddit story TikToks)
- **Color:** White with 3px black outline
- **Shadow:** Semi-transparent black for readability over any background
- **Alignment:** Center-center (5 in ASS format)
- **Margin bottom:** 40px (above the code overlay zone)

## Code Overlay Style

Code snippets are **read from the actual repo files** (not hardcoded in scripts). Rendered as images via Pillow:
- **Background:** Dark (#1E1E2E) with rounded corners + macOS window dots
- **Font:** Consolas / Cascadia Code / JetBrains Mono, **26pt** (much bigger — must be readable on phone)
- **Max lines:** 12 (truncate longer snippets with `// ...`)
- **Syntax highlighting:** Catppuccin theme (keywords blue, strings green, comments gray)
- **Position:** Bottom third of screen, centered
- **Size:** 90% of video width, auto height
- **Border:** 2px subtle border with rounded corners
- **Caption:** Below code block, slightly smaller font, light gray

## Background Video Rules

- Pick randomly from `assets/1.mp4`, `2.mp4`, `3.mp4`
- Loop if audio is longer than video
- Crop to 9:16 (vertical/portrait) for TikTok format
- Dim brightness slightly (~88%) so text overlays pop
- Think Subway Surfers / Minecraft parkour / satisfying clips energy
