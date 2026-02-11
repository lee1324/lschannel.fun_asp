#!/usr/bin/env python3
"""
Compress video file to target size using ffmpeg or alternative methods.
"""
import os
import subprocess
import sys

def get_duration_opencv(input_file):
    """Get video duration using OpenCV fallback."""
    try:
        import cv2
        cap = cv2.VideoCapture(input_file)
        if not cap.isOpened():
            return None
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        if fps and fps > 0 and frame_count >= 0:
            return frame_count / fps
    except Exception:
        pass
    return None

def compress_with_ffmpeg(input_file, output_file, target_size_mb=5):
    """Compress video using ffmpeg to target size."""
    duration = None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", input_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
    except Exception:
        pass
    if duration is None:
        duration = get_duration_opencv(input_file)
    if duration is None:
        print("Could not get video duration (need ffprobe or OpenCV)")
        return False

    # Calculate target bitrate (in kbps)
    target_bitrate_kbps = int((target_size_mb * 8 * 1024) / duration * 0.9)
    video_bitrate = max(target_bitrate_kbps - 128, 500)

    print(f"Target size: {target_size_mb}MB, Duration: {duration:.1f}s")
    print(f"Target bitrate: {target_bitrate_kbps}kbps (video: {video_bitrate}kbps, audio: 128kbps)")

    try:
        subprocess.run(
            ["ffmpeg", "-i", input_file,
             "-c:v", "libx264",
             "-b:v", f"{video_bitrate}k",
             "-maxrate", f"{video_bitrate}k",
             "-bufsize", f"{video_bitrate * 2}k",
             "-c:a", "aac",
             "-b:a", "128k",
             "-movflags", "+faststart",
             "-y", output_file],
            check=True,
            timeout=600
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error: {e}")
        return False
    except FileNotFoundError:
        print("ffmpeg not found. Install with: brew install ffmpeg")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compress_video.py <input_file> [output_file] [target_size_mb]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace(".m4v", "_compressed.m4v").replace(".MP4", "_compressed.MP4").replace(".mp4", "_compressed.mp4")
    target_size_mb = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    print(f"Compressing {input_file} to {output_file} (target: {target_size_mb}MB)...")
    
    if compress_with_ffmpeg(input_file, output_file, target_size_mb):
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"✓ Success! Output file: {output_file} ({size_mb:.2f}MB)")
    else:
        print("✗ Compression failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
