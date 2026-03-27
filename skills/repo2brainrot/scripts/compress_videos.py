"""
compress_videos.py — Re-encode existing brainrot videos to smaller file sizes.

Targets: 720p (1280x720), CRF 28, preset medium → typically 5-10 MB per episode.

Usage:
    python skills/repo2brainrot/scripts/compress_videos.py output/my-repo/videos/
    python skills/repo2brainrot/scripts/compress_videos.py output/my-repo/videos/ --crf 30 --width 720
    python skills/repo2brainrot/scripts/compress_videos.py output/my-repo/videos/ --dry-run
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def get_video_info(path: str) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,bit_rate",
            "-show_entries", "format=duration,size",
            "-of", "default=noprint_wrappers=1",
            path,
        ],
        capture_output=True, text=True, check=True,
    )
    info = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k.strip()] = v.strip()
    return info


def compress_video(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
    crf: int,
) -> None:
    """Re-encode a video at target resolution and CRF."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                   f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",  # web-optimized: moov atom at front
            output_path,
        ],
        check=True,
        capture_output=True,
    )


def human_size(bytes: int) -> str:
    mb = bytes / 1_048_576
    return f"{mb:.1f} MB"


def main():
    parser = argparse.ArgumentParser(description="Compress brainrot output videos")
    parser.add_argument("videos_dir", help="Directory containing ep*.mp4 files")
    parser.add_argument("--crf", type=int, default=28, help="CRF quality (default 28; higher=smaller)")
    parser.add_argument("--width", type=int, default=720, help="Output width (default 720)")
    parser.add_argument("--height", type=int, default=1280, help="Output height (default 1280)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be compressed, don't do it")
    parser.add_argument("--skip-full-feed", action="store_true", default=True, help="Skip full_feed.mp4 (re-concat instead)")
    args = parser.parse_args()

    videos_dir = Path(args.videos_dir)
    if not videos_dir.exists():
        print(f"Directory not found: {videos_dir}", file=sys.stderr)
        sys.exit(1)

    # Find all episode videos (skip full_feed — re-concat after)
    mp4s = sorted(videos_dir.glob("ep*.mp4"))
    if not mp4s:
        print(f"No ep*.mp4 files found in {videos_dir}")
        sys.exit(1)

    print(f"Found {len(mp4s)} episode(s) in {videos_dir}")
    print(f"Target: {args.width}x{args.height}, CRF {args.crf}, preset medium")
    print()

    total_before = 0
    total_after = 0

    for mp4 in mp4s:
        size_before = mp4.stat().st_size
        total_before += size_before

        if args.dry_run:
            print(f"  [dry-run] {mp4.name}  {human_size(size_before)}")
            continue

        print(f"  Compressing {mp4.name}  ({human_size(size_before)}) ...", end=" ", flush=True)

        # Write to temp file first, then replace
        tmp = mp4.with_suffix(".tmp.mp4")
        try:
            compress_video(str(mp4), str(tmp), args.width, args.height, args.crf)
            size_after = tmp.stat().st_size
            total_after += size_after
            saving = (1 - size_after / size_before) * 100
            mp4.unlink()
            tmp.rename(mp4)
            print(f"→ {human_size(size_after)}  ({saving:.0f}% smaller)")
        except subprocess.CalledProcessError as e:
            print(f"FAILED")
            print(f"    stderr: {e.stderr.decode()[-300:]}", file=sys.stderr)
            if tmp.exists():
                tmp.unlink()

    if not args.dry_run and total_after > 0:
        print()
        print(f"  Before: {human_size(total_before)}")
        print(f"  After:  {human_size(total_after)}")
        print(f"  Saved:  {human_size(total_before - total_after)}  ({(1 - total_after/total_before)*100:.0f}% reduction)")

        # Re-concat full_feed.mp4 from compressed episodes
        full_feed = videos_dir / "full_feed.mp4"
        filelist = videos_dir / "filelist.txt"
        if filelist.exists() and len(mp4s) > 1:
            print(f"\n  Rebuilding full_feed.mp4 from compressed episodes...")
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(filelist), "-c", "copy", str(full_feed)],
                check=True, capture_output=True,
            )
            print(f"  ✓ full_feed.mp4  ({human_size(full_feed.stat().st_size)})")


if __name__ == "__main__":
    main()
