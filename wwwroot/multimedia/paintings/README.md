# Paintings Cover Generation

This folder contains scripts to generate thumbnail covers for paintings to improve loading performance.

## Installation

### Install Pillow (Required)

If you encounter proxy issues with pip, try these solutions:

**Option 1: Configure pip to bypass proxy**
```bash
pip3 install --user --proxy="" Pillow
```

**Option 2: Use pip with no proxy**
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
pip3 install --user Pillow
```

**Option 3: Install via conda (if available)**
```bash
conda install pillow
```

**Option 4: Download and install manually**
1. Download Pillow wheel from: https://pypi.org/project/Pillow/#files
2. Install with: `pip3 install --user /path/to/Pillow-*.whl`

### Install pillow-heif (Optional, for HEIC support)

```bash
pip3 install --user pillow-heif
```

## Usage

Generate covers for all images:
```bash
cd wwwroot/multimedia/paintings
python3 generate_covers.py
```

The script will:
- Create square thumbnails (250x250px) in `covers_generated/`
- Skip images that already have up-to-date covers
- Handle JPG, PNG, and HEIC formats

## Auto-generation

Covers are automatically generated when you click "🔄 Reload Paintings" in the manager page, if Pillow is installed.
