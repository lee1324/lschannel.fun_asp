#!/usr/bin/env python3
"""
Generate square thumbnails (covers) for each image in images/ and save as covers_generated/xxx_cover.png.
Uses PIL/Pillow for image processing. Install with: pip install Pillow
"""
import os
import sys
from PIL import Image

def generate_cover(image_path: str, out_path: str, size: int = 250) -> bool:
    """
    Generate a square thumbnail cover from an image.
    Args:
        image_path: Path to the source image
        out_path: Path to save the cover
        size: Size of the square thumbnail (default 250x250)
    Returns:
        True if successful, False otherwise
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Convert to RGB if necessary (handles RGBA, P mode, etc.)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate crop to make it square (center crop)
        width, height = img.size
        if width > height:
            # Landscape: crop width
            left = (width - height) // 2
            right = left + height
            top = 0
            bottom = height
        else:
            # Portrait or square: crop height
            top = (height - width) // 2
            bottom = top + width
            left = 0
            right = width
        
        # Crop to square
        img = img.crop((left, top, right, bottom))
        
        # Resize to target size
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Save as PNG
        img.save(out_path, 'PNG', optimize=True)
        return True
    except Exception as e:
        print(f"  Error processing {image_path}: {e}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, "images")
    out_dir = os.path.join(script_dir, "covers_generated")
    
    # Check if PIL is available
    try:
        from PIL import Image
    except ImportError:
        print("PIL/Pillow is not available.")
        print("\nTo install Pillow, try one of these methods:")
        print("  1. pip3 install --user Pillow")
        print("  2. python3 -m pip install --user Pillow")
        print("  3. If proxy issues occur, configure pip to bypass proxy or install manually")
        print("\nFor HEIC support (optional), also install:")
        print("  pip3 install --user pillow-heif")
        sys.exit(1)
    
    os.makedirs(out_dir, exist_ok=True)
    
    if not os.path.isdir(images_dir):
        print("No images/ folder found.")
        return
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG', '.heic', '.HEIC'}
    image_files = [f for f in os.listdir(images_dir) 
                   if any(f.lower().endswith(ext.lower()) for ext in image_extensions)]
    
    if not image_files:
        print("No image files found in images/.")
        return
    
    print(f"Found {len(image_files)} images. Generating covers...")
    
    for img_file in sorted(image_files):
        base, ext = os.path.splitext(img_file)
        img_path = os.path.join(images_dir, img_file)
        out_path = os.path.join(out_dir, base + "_cover.png")
        
        # Skip if cover already exists and is newer than source
        if os.path.exists(out_path):
            if os.path.getmtime(out_path) >= os.path.getmtime(img_path):
                print(f"Skipping {img_file} (cover already up to date)")
                continue
        
        print(f"Generating cover: {img_file} -> {os.path.basename(out_path)}")
        
        # Handle HEIC files (may need special handling)
        if ext.lower() in ['.heic', '.heif']:
            # Try to use pillow-heif if available
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
            except ImportError:
                print(f"  WARNING: HEIC support requires pillow-heif. Install with: pip install pillow-heif")
                print(f"  Skipping {img_file}")
                continue
        
        ok = generate_cover(img_path, out_path)
        if ok:
            print(f"  OK")
        else:
            print(f"  FAILED")
    
    print("Done.")

if __name__ == "__main__":
    main()
