#!/usr/bin/env python3
"""
Rename v*.MP4 / v*.mp4 files by parsing the title from the first frame (OCR).
"""
from pathlib import Path
import re
import sys

try:
    import cv2
    import easyocr
except ImportError as e:
    print("Install dependencies: pip install -r requirements.txt", file=sys.stderr)
    raise SystemExit(1) from e


# Characters invalid in filenames (Windows / macOS)
INVALID_CHARS = re.compile(r'[/\\:*?"<>|\n\r\t]+')


def sanitize_filename(title: str) -> str:
    """Make a string safe for use as filename (strip, replace invalid chars)."""
    s = title.strip()
    s = INVALID_CHARS.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or "untitled"


def extract_first_frame(video_path: Path):
    """Read first frame from video; return numpy array or None."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None


def parse_title_from_frame(frame, reader) -> str:
    """
    Run OCR on frame; return a single title string.
    Prefer top-most text line(s), then join.
    """
    results = reader.readtext(frame)
    if not results:
        return ""
    # Each item: (bbox, text, confidence). bbox is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    # Sort by top-left y (smaller y = higher on screen)
    def top_y(item):
        bbox = item[0]
        return min(p[1] for p in bbox)

    results.sort(key=top_y)
    texts = [item[1].strip() for item in results if item[1].strip()]
    if not texts:
        return ""
    # Use first line as title; if very short, add next line (e.g. "角\n度&弧")
    title = texts[0]
    if len(title) <= 2 and len(texts) > 1:
        title = title + texts[1]
    elif len(texts) > 1 and len(texts[0]) < 4:
        # Possibly two-line title like "电子移速\n电流形成速度"
        title = "".join(texts[:2])
    return title


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Rename v*.MP4 by title parsed from first frame (OCR).")
    ap.add_argument("--dry-run", action="store_true", help="Only print renames, do not rename.")
    args = ap.parse_args()
    dry_run = args.dry_run

    root = Path(__file__).resolve().parent
    # All MP4 files whose basename starts with 'v'
    candidates = []
    for p in root.iterdir():
        if not p.is_file():
            continue
        if p.suffix.upper() != ".MP4":
            continue
        if p.name.upper().startswith("V"):
            candidates.append(p)

    if not candidates:
        print("No v*.MP4 files found.")
        return

    print("Loading OCR model (ch_sim + en)...")
    reader = easyocr.Reader(["ch_sim", "en"])

    for video_path in sorted(candidates):
        name = video_path.name
        print(f"\n--- {name}")
        frame = extract_first_frame(video_path)
        if frame is None:
            print("  Could not read first frame, skip.")
            continue
        title = parse_title_from_frame(frame, reader)
        if not title:
            print("  No text detected on first frame, skip.")
            continue
        safe = sanitize_filename(title)
        new_name = safe + video_path.suffix
        new_path = video_path.parent / new_name
        if new_path == video_path:
            print("  Title matches current name, skip.")
            continue
        if new_path.exists():
            print(f"  Target already exists: {new_name}, skip.")
            continue
        print(f"  Title: {title!r} -> {new_name}")
        if dry_run:
            print("  [dry-run] would rename.")
        else:
            video_path.rename(new_path)
            print("  Renamed.")

    print("\nDone.")


if __name__ == "__main__":
    main()
