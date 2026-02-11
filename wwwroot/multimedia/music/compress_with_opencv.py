#!/usr/bin/env python3
"""
Basic video compression using OpenCV (limited quality, but works without ffmpeg).
Note: This is a basic implementation - ffmpeg provides much better compression.
"""
import cv2
import os
import sys

def compress_video_opencv(input_file, output_file, target_size_mb=5):
    """Compress video using OpenCV - basic implementation."""
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return False
    
    cap = cv2.VideoCapture(input_file)
    if not cap.isOpened():
        print("Error: Could not open video file")
        return False
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    
    print(f"Input: {width}x{height}, {fps}fps, {duration:.1f}s")
    
    # Calculate target bitrate
    target_bitrate = int((target_size_mb * 8 * 1024 * 1024) / duration * 0.9) if duration > 0 else 2000000
    print(f"Target size: {target_size_mb}MB, Target bitrate: {target_bitrate // 1000}kbps")
    
    # Scale down if too large (reduce resolution for better compression)
    # Keep aspect ratio, max width 1280
    scale = min(1.0, 1280.0 / width) if width > 1280 else 1.0
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    if scale < 1.0:
        print(f"Scaling down to {new_width}x{new_height} for better compression")
    
    # Set up video writer with compression - try different codecs
    codecs_to_try = [
        ('mp4v', cv2.VideoWriter_fourcc(*'mp4v')),
        ('avc1', cv2.VideoWriter_fourcc(*'avc1')),
        ('XVID', cv2.VideoWriter_fourcc(*'XVID')),
        ('MJPG', cv2.VideoWriter_fourcc(*'MJPG')),
    ]
    
    out = None
    used_codec = None
    for codec_name, fourcc in codecs_to_try:
        test_out = cv2.VideoWriter(output_file, fourcc, fps, (new_width, new_height))
        if test_out.isOpened():
            out = test_out
            used_codec = codec_name
            print(f"Using codec: {codec_name}")
            break
        test_out.release()
    
    if out is None or not out.isOpened():
        print("Error: Could not create output video with any available codec")
        print("OpenCV may not have video codec support. Consider installing ffmpeg.")
        cap.release()
        return False
    
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize if needed
        if scale < 1.0:
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        out.write(frame)
        frame_num += 1
        if frame_num % 30 == 0:
            print(f"Processed {frame_num}/{frame_count} frames...", end='\r')
    
    cap.release()
    out.release()
    
    output_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n✓ Done! Output: {output_file} ({output_size_mb:.2f}MB)")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 compress_with_opencv.py <input_file> [output_file] [target_size_mb]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace(".m4v", "_compressed.m4v").replace(".mp4", "_compressed.mp4")
    target_size_mb = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    
    compress_video_opencv(input_file, output_file, target_size_mb)
