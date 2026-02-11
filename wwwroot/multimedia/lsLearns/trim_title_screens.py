#!/usr/bin/env python3
"""
Backup lsLearns/videos and remove the static title screen from the start
of each video, saving trimmed videos back to the same paths.

For each video:
- Use analyze_title_screens.analyze_title_screen() to get (fps, static_frames)
- Compute start_time = static_frames / fps (in seconds)
- Run ffmpeg to trim the first start_time seconds and rewrite the file.

Backup:
- Create a sibling folder videos_backup_<timestamp> and copy all original
  videos there before modifying anything.
"""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from analyze_title_screens import analyze_title_screen, VIDEO_DIR


def ensure_ffmpeg() -> None:
    """Check that ffmpeg is available; raise if not."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError("ffmpeg not available (non-zero exit)")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found. Please install it (e.g., brew install ffmpeg).")


def backup_videos(videos_dir: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = videos_dir.parent / f"videos_backup_{ts}"
    print(f"Backing up videos from {videos_dir} to {backup_dir} ...")
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(videos_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in {".mp4", ".m4v"}:
            target = backup_dir / f.name
            print(f"  Copying {f.name} -> {target.name}")
            shutil.copy2(f, target)
    return backup_dir


def trim_video(input_path: Path, output_path: Path, start_time: float) -> None:
    """
    Use ffmpeg to trim the first start_time seconds.
    We re-encode video+audio to be safe (copy sometimes fails with non-keyframe cuts).
    """
    # ffmpeg command:
    # ffmpeg -y -ss <start_time> -i input -c:v libx264 -c:a aac -movflags +faststart output
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{start_time:.3f}",
        "-i",
        str(input_path),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    print(f"    ffmpeg trimming from {start_time:.3f}s ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    ffmpeg failed for {input_path.name}: {result.stderr}")
        raise RuntimeError(f"ffmpeg failed for {input_path.name}")


def main() -> None:
    videos_dir = VIDEO_DIR
    if not videos_dir.is_dir():
        print(f"Video directory not found: {videos_dir}")
        return

    ensure_ffmpeg()

    files = sorted(
        f for f in videos_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".mp4", ".m4v"}
    )
    if not files:
        print("No .mp4/.m4v files found in lsLearns/videos/")
        return

    # Backup originals first
    backup_dir = backup_videos(videos_dir)
    print(f"Backup complete: {backup_dir}")

    print("\nTrimming title screens from videos...")
    for f in files:
        fps, static_frames = analyze_title_screen(f)
        if static_frames <= 0 or fps <= 0:
            print(f"- {f.name}: skipping (could not determine static title length)")
            continue
        start_time = static_frames / fps
        print(f"- {f.name}: static {static_frames} frame(s), fps ~ {fps:.2f}, cut start at {start_time:.3f}s")

        tmp_output = f.with_suffix(".trimmed.tmp" + f.suffix)
        try:
            trim_video(f, tmp_output, start_time)
            # Replace original atomically
            f.unlink()
            tmp_output.rename(f)
            print(f"    Replaced original with trimmed version.")
        except Exception as e:
            print(f"    Error trimming {f.name}: {e}")
            if tmp_output.exists():
                tmp_output.unlink()

    print("\nDone. Original videos are backed up in:")
    print(f"  {backup_dir}")


if __name__ == "__main__":
    main()

