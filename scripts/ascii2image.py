#!/usr/bin/env python3
"""
Script: ASCII Art to Image Converter
Description: Extracts ASCII art diagrams from markdown and converts them to PNG images
             for clean PDF rendering.

Usage:
    python ascii2img.py input.md output.md --img-dir ./images
    
This script:
1. Finds ASCII art blocks (code blocks containing box-drawing characters)
2. Renders them as PNG images using DejaVu Sans Mono font
3. Outputs modified markdown with image references
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

# Box-drawing characters that indicate ASCII art
BOX_CHARS = set("┌┐└┘├┤┬┴┼─│═║╔╗╚╝╠╣╦╩╬▼▲◄►")

# Font settings
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_SIZE = 14
LINE_HEIGHT = 18
PADDING = 20
BG_COLOR = "#f8f9fa"  # Light gray background
TEXT_COLOR = "#1a1a2e"  # Dark text
BORDER_COLOR = "#dee2e6"  # Border color


def is_ascii_art(text: str) -> bool:
    """Check if text contains ASCII art box-drawing characters."""
    return any(char in BOX_CHARS for char in text)


def extract_code_blocks(markdown: str) -> list[tuple[int, int, str, str]]:
    """
    Extract code blocks from markdown.
    Returns list of (start_pos, end_pos, language, content) tuples.
    """
    # Match fenced code blocks: ```language\n...\n```
    pattern = r"```(\w*)\n(.*?)```"
    blocks = []
    
    for match in re.finditer(pattern, markdown, re.DOTALL):
        start = match.start()
        end = match.end()
        lang = match.group(1)
        content = match.group(2)
        
        # Only process blocks that look like ASCII art
        if is_ascii_art(content) and lang in ("", "text", "ascii", "diagram"):
            blocks.append((start, end, lang, content))
    
    return blocks


def render_ascii_to_image(text: str, output_path: Path) -> bool:
    """Render ASCII art text to a PNG image."""
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except OSError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    lines = text.rstrip().split("\n")
    
    # Calculate image dimensions
    max_width = 0
    for line in lines:
        bbox = font.getbbox(line)
        width = bbox[2] - bbox[0] if bbox else len(line) * 8
        max_width = max(max_width, width)
    
    img_width = max_width + (PADDING * 2)
    img_height = (len(lines) * LINE_HEIGHT) + (PADDING * 2)
    
    # Create image with background
    img = Image.new("RGB", (img_width, img_height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle(
        [1, 1, img_width - 2, img_height - 2],
        outline=BORDER_COLOR,
        width=1
    )
    
    # Draw text
    y = PADDING
    for line in lines:
        draw.text((PADDING, y), line, font=font, fill=TEXT_COLOR)
        y += LINE_HEIGHT
    
    # Save image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    return True


def process_markdown(
    input_text: str,
    img_dir: Path,
    base_name: str = "diagram"
) -> tuple[str, int]:
    """
    Process markdown, converting ASCII art blocks to images.
    Returns (modified_markdown, num_conversions).
    """
    blocks = extract_code_blocks(input_text)
    
    if not blocks:
        return input_text, 0
    
    # Process blocks in reverse order to preserve positions
    result = input_text
    converted = 0
    
    for start, end, lang, content in reversed(blocks):
        # Generate unique filename based on content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        img_name = f"{base_name}_{content_hash}.png"
        img_path = img_dir / img_name
        
        if render_ascii_to_image(content, img_path):
            # Replace code block with image reference
            # Use relative path for markdown
            rel_path = img_path.name
            replacement = f"![Diagram]({img_dir.name}/{rel_path})"
            result = result[:start] + replacement + result[end:]
            converted += 1
    
    return result, converted


def process_file(
    input_path: Path,
    output_path: Path,
    img_dir: Path
) -> int:
    """Process a single markdown file."""
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    base_name = input_path.stem.replace("-", "_")
    processed, num_converted = process_markdown(content, img_dir, base_name)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(processed)
    
    return num_converted


def main():
    parser = argparse.ArgumentParser(
        description="Convert ASCII art in markdown to PNG images"
    )
    parser.add_argument("input", help="Input markdown file or '-' for stdin")
    parser.add_argument("output", help="Output markdown file or '-' for stdout")
    parser.add_argument(
        "--img-dir",
        default="./diagrams",
        help="Directory to save generated images (default: ./diagrams)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    img_dir = Path(args.img_dir)
    
    # Read input
    if args.input == "-":
        content = sys.stdin.read()
        base_name = "diagram"
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
        base_name = input_path.stem.replace("-", "_")
    
    # Process
    processed, num_converted = process_markdown(content, img_dir, base_name)
    
    # Write output
    if args.output == "-":
        print(processed)
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(processed)
    
    if args.verbose:
        print(f"Converted {num_converted} ASCII art blocks to images", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
