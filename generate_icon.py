#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generate a simple icon for CountyDataSync
"""

import os
from PIL import Image, ImageDraw, ImageFont


def generate_icon(size=256, filename='generated-icon.png'):
    """Generate a simple icon for CountyDataSync."""
    # Create a blank image with a blue background
    img = Image.new('RGB', (size, size), color=(20, 40, 100))
    draw = ImageDraw.Draw(img)
    
    # Draw a stylized 'C' and 'D' for CountyDataSync
    margin = size // 8
    draw.ellipse(
        [(margin, margin), (size - margin, size - margin)],
        outline=(240, 240, 240),
        width=size // 25
    )
    
    # Draw data flow lines
    line_width = size // 30
    for i in range(3):
        y_pos = size // 3 + i * (size // 6)
        # Left to right line
        draw.line(
            [(size // 3, y_pos), (2 * size // 3, y_pos)],
            fill=(220, 220, 240),
            width=line_width
        )
        # Arrow head
        draw.polygon(
            [
                (2 * size // 3 + line_width, y_pos),
                (2 * size // 3 - line_width, y_pos - line_width),
                (2 * size // 3 - line_width, y_pos + line_width)
            ],
            fill=(220, 220, 240)
        )
    
    # Save the image
    img.save(filename)
    print(f"Generated icon at {filename}")
    return filename


if __name__ == "__main__":
    generate_icon()