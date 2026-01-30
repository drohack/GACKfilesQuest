#!/usr/bin/env python3
"""
Generate QR codes for all GACKfiles quests and overlay them on the hand PNG
"""
import sqlite3
import qrcode
from PIL import Image, ImageDraw, ImageFilter
import os

# Configuration
DATABASE = 'app/database.db'
HAND_PNG = 'app/QR/GACKfiles_QR_hand.png'
OUTPUT_DIR = 'app/QR/generated'
BASE_URL = 'https://gackfiles.saltychart.net/qr/'

# QR Code positioning (adjust these to fit the transparent square)
QR_POSITION = (None, None)  # Will be calculated from transparent area
QR_SIZE = None  # Will be calculated from transparent area

def get_average_colors(hand_image):
    """Extract average light and dark colors from the hand PNG"""
    pixels = list(hand_image.getdata())

    # Filter out transparent pixels and separate by brightness
    light_pixels = []
    dark_pixels = []

    for pixel in pixels:
        if len(pixel) == 4 and pixel[3] > 128:  # Not transparent
            r, g, b, a = pixel
            brightness = (r + g + b) / 3
            if brightness > 128:
                light_pixels.append((r, g, b))
            else:
                dark_pixels.append((r, g, b))

    # Calculate averages
    if light_pixels:
        avg_light = tuple(sum(c) // len(light_pixels) for c in zip(*light_pixels))
    else:
        avg_light = (230, 220, 200)  # Default beige

    if dark_pixels:
        avg_dark = tuple(sum(c) // len(dark_pixels) for c in zip(*dark_pixels))
    else:
        avg_dark = (80, 20, 20)  # Default dark red

    return avg_light, avg_dark

def find_transparent_area(hand_image):
    """Find the bounding box of the transparent square"""
    width, height = hand_image.size
    pixels = hand_image.load()

    # Find transparent region bounds
    min_x, min_y = width, height
    max_x, max_y = 0, 0

    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if len(pixel) == 4 and pixel[3] < 128:  # Transparent
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if min_x < max_x and min_y < max_y:
        return (min_x, min_y, max_x - min_x, max_y - min_y)
    else:
        # Default to center if no transparent area found
        return (width // 4, height // 4, width // 2, height // 2)

def add_texture_to_qr(qr_image, background_color):
    """Add slight texture to QR code background"""
    # Create a subtle noise texture
    width, height = qr_image.size
    texture = Image.new('RGBA', (width, height), background_color)

    # Add very subtle random variations
    import random
    pixels = texture.load()
    for y in range(height):
        for x in range(width):
            r, g, b = background_color
            # Add small random variation
            variation = random.randint(-10, 10)
            pixels[x, y] = (
                max(0, min(255, r + variation)),
                max(0, min(255, g + variation)),
                max(0, min(255, b + variation)),
                255
            )

    return texture

def generate_qr_with_overlay(scan_code, title, hand_image, light_color, dark_color, output_path):
    """Generate a QR code and overlay it on the hand PNG"""
    # Generate QR code
    url = f"{BASE_URL}{scan_code}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Create QR image with custom colors
    qr_img = qr.make_image(fill_color=dark_color, back_color=light_color)
    qr_img = qr_img.convert('RGBA')

    # Find transparent area in hand image
    trans_x, trans_y, trans_w, trans_h = find_transparent_area(hand_image)

    # Resize QR to fit in transparent area (with some padding)
    padding = 20
    qr_size = min(trans_w - padding, trans_h - padding)
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    # Create output image
    result = hand_image.copy()

    # Center QR in transparent area
    qr_x = trans_x + (trans_w - qr_size) // 2
    qr_y = trans_y + (trans_h - qr_size) // 2

    # Paste QR code
    result.paste(qr_img, (qr_x, qr_y), qr_img)

    # Save result
    result.save(output_path, 'PNG')
    print(f"Generated: {output_path}")

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load hand PNG
    print(f"Loading hand PNG from: {HAND_PNG}")
    hand_image = Image.open(HAND_PNG).convert('RGBA')

    # Get colors from hand image
    print("Analyzing hand PNG colors...")
    light_color, dark_color = get_average_colors(hand_image)
    # Make the dark color much darker for better QR code visibility
    dark_color = tuple(max(0, c // 3) for c in dark_color)  # Divide by 3 to make it much darker
    print(f"Light color (QR background): RGB{light_color}")
    print(f"Dark color (QR foreground): RGB{dark_color}")

    # Connect to database
    print(f"\nConnecting to database: {DATABASE}")
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    # Get all videos
    videos = conn.execute('SELECT id, title, scan_code, is_bonus FROM videos ORDER BY id').fetchall()
    conn.close()

    print(f"\nGenerating QR codes for {len(videos)} quests...\n")

    # Generate QR codes
    for video in videos:
        # Create safe filename
        safe_title = video['title'].replace(' ', '_').replace('/', '_')
        filename = f"{video['id']:02d}_{safe_title}.png"
        output_path = os.path.join(OUTPUT_DIR, filename)

        print(f"[{video['id']}] {video['title']} ({video['scan_code']})")
        generate_qr_with_overlay(
            video['scan_code'],
            video['title'],
            hand_image,
            light_color,
            dark_color,
            output_path
        )

    print(f"\n[OK] All QR codes generated in: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
