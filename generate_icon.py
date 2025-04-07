"""
Generate a simple icon for CountyDataSync
"""
import os
import sys
from PIL import Image, ImageDraw

def generate_icon(size=256, filename='generated-icon.png'):
    """Generate a simple icon for CountyDataSync."""
    # Create a new image with a white background
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a blue circle for the background
    circle_radius = size // 2 - 4
    circle_center = (size // 2, size // 2)
    circle_bbox = (
        circle_center[0] - circle_radius,
        circle_center[1] - circle_radius,
        circle_center[0] + circle_radius,
        circle_center[1] + circle_radius
    )
    draw.ellipse(circle_bbox, fill=(41, 128, 185, 255))
    
    # Draw a stylized "CDS" text or map icon
    # Use a simple polygon to represent a map/parcel
    map_width = int(size * 0.5)
    map_height = int(size * 0.4)
    map_top_left = (
        circle_center[0] - map_width // 2,
        circle_center[1] - map_height // 2
    )
    
    # Draw a stylized map/document icon
    draw.rectangle(
        (map_top_left[0], map_top_left[1], 
         map_top_left[0] + map_width, map_top_left[1] + map_height),
        fill=(236, 240, 241, 255),
        outline=(52, 73, 94, 255),
        width=int(size * 0.02)
    )
    
    # Add grid lines to represent a map
    line_spacing = map_height // 3
    for i in range(1, 3):
        # Horizontal lines
        draw.line(
            (map_top_left[0], map_top_left[1] + i * line_spacing,
             map_top_left[0] + map_width, map_top_left[1] + i * line_spacing),
            fill=(52, 73, 94, 255),
            width=int(size * 0.01)
        )
    
    line_spacing = map_width // 3
    for i in range(1, 3):
        # Vertical lines
        draw.line(
            (map_top_left[0] + i * line_spacing, map_top_left[1],
             map_top_left[0] + i * line_spacing, map_top_left[1] + map_height),
            fill=(52, 73, 94, 255),
            width=int(size * 0.01)
        )
    
    # Add a synchronize arrow icon
    arrow_size = int(size * 0.15)
    arrow_center = (
        circle_center[0] + map_width // 2 + arrow_size // 2,
        circle_center[1] + map_height // 2 + arrow_size // 2
    )
    
    # Draw circular arrow
    draw.arc(
        (arrow_center[0] - arrow_size, arrow_center[1] - arrow_size,
         arrow_center[0] + arrow_size, arrow_center[1] + arrow_size),
        start=0, end=270,
        fill=(46, 204, 113, 255),
        width=int(size * 0.06)
    )
    
    # Draw arrow head
    head_size = int(size * 0.08)
    draw.polygon(
        [
            (arrow_center[0], arrow_center[1] - arrow_size),
            (arrow_center[0] - head_size, arrow_center[1] - arrow_size + head_size),
            (arrow_center[0] + head_size, arrow_center[1] - arrow_size + head_size)
        ],
        fill=(46, 204, 113, 255)
    )
    
    # Save the image
    img.save(filename)
    print(f"Icon generated: {filename}")
    
    return filename

if __name__ == "__main__":
    try:
        generate_icon()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)