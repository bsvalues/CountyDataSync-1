#!/usr/bin/env python3
"""
Generate a simple icon for CountyDataSync
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_icon(size=256, filename='generated-icon.png'):
    """Generate a simple icon for CountyDataSync."""
    logger.info(f"Generating icon with size {size}x{size}")
    
    # Create a new image with white background
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a filled circle for the background
    circle_color = (41, 128, 185)  # Blue
    padding = int(size * 0.1)
    draw.ellipse(
        [(padding, padding), (size - padding, size - padding)],
        fill=circle_color
    )
    
    # Draw a map-like grid pattern
    grid_color = (255, 255, 255, 128)  # Semi-transparent white
    grid_spacing = size // 8
    
    # Horizontal lines
    for y in range(grid_spacing, size, grid_spacing):
        draw.line([(padding, y), (size - padding, y)], fill=grid_color, width=2)
    
    # Vertical lines
    for x in range(grid_spacing, size, grid_spacing):
        draw.line([(x, padding), (x, size - padding)], fill=grid_color, width=2)
    
    # Draw "CDS" text in the center
    text_color = (255, 255, 255, 230)  # Almost opaque white
    
    # Try to use a system font, or fall back to a default font
    try:
        # Attempt to find a suitable font
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
            'C:\\Windows\\Fonts\\Arial.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size=int(size * 0.4))
                break
        
        if font is None:
            # Fall back to default font
            font = ImageFont.load_default()
            logger.warning("Using default font as no system fonts were found")
    except Exception as e:
        # If font loading fails, use the default font
        font = ImageFont.load_default()
        logger.warning(f"Error loading font: {e}. Using default font instead.")
    
    # Calculate text position to center it
    text = "CDS"
    try:
        # For newer versions of Pillow
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        # For older versions of Pillow
        text_width, text_height = draw.textsize(text, font=font)
    
    text_position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(text_position, text, fill=text_color, font=font)
    
    # Save the image
    try:
        image.save(filename)
        logger.info(f"Icon saved as {filename}")
        return os.path.abspath(filename)
    except Exception as e:
        logger.error(f"Error saving icon: {e}")
        return None

if __name__ == "__main__":
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Generate an icon for CountyDataSync")
    parser.add_argument("--size", type=int, default=256, help="Icon size in pixels (default: 256)")
    parser.add_argument("--output", type=str, default="generated-icon.png", help="Output filename (default: generated-icon.png)")
    args = parser.parse_args()
    
    # Generate the icon
    icon_path = generate_icon(size=args.size, filename=args.output)
    
    if icon_path:
        print(f"Icon generated successfully: {icon_path}")
        sys.exit(0)
    else:
        print("Failed to generate icon")
        sys.exit(1)