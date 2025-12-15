#!/usr/bin/env python3
"""Generate all required favicon and icon sizes from source Miles logo."""

import os

from PIL import Image

# Source image
SOURCE = "../miles.png"
OUTPUT_DIR = "branding/favicons"

# Icon sizes needed
ICONS = {
    "favicon.png": 32,
    "favicon-96x96.png": 96,
    "apple-touch-icon.png": 180,
    "web-app-manifest-192x192.png": 192,
    "web-app-manifest-512x512.png": 512,
    "splash.png": 512,
    "splash-dark.png": 512,
}


def generate_icons():
    """Generate all icon sizes from source image."""

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Open source image
    print(f"Opening source image: {SOURCE}")
    img = Image.open(SOURCE)
    print(f"Source image size: {img.size}")
    print(f"Source image mode: {img.mode}")

    # Generate each icon size
    for filename, size in ICONS.items():
        print(f"Generating {filename} ({size}x{size})...")

        # Resize image maintaining aspect ratio and centering on transparent background
        icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))

        # Calculate scaling to fit within size while maintaining aspect ratio
        img_ratio = img.width / img.height
        if img_ratio > 1:
            # Wider than tall
            new_width = size
            new_height = int(size / img_ratio)
        else:
            # Taller than wide
            new_height = size
            new_width = int(size * img_ratio)

        # Resize source image
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center on transparent background
        x_offset = (size - new_width) // 2
        y_offset = (size - new_height) // 2
        icon.paste(resized, (x_offset, y_offset), resized if resized.mode == "RGBA" else None)

        # Save icon
        output_path = os.path.join(OUTPUT_DIR, filename)
        icon.save(output_path, "PNG")
        print(f"  ✓ Saved {output_path}")

    print("\n✅ All icons generated successfully!")
    print("\nNext steps:")
    print("1. Run ./apply_branding.sh to apply branding to Open Web UI")
    print("2. (Optional) Create miles.svg for vector logo")


if __name__ == "__main__":
    generate_icons()
