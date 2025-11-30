#!/usr/bin/env python3
"""
QR Code Generator for Video Quest
Generates QR codes for each video in the database
Requires: pip install qrcode[pil]
"""

import sqlite3
import qrcode
import os
import sys

DATABASE = 'app/database.db'
OUTPUT_DIR = 'qrcodes'
BASE_URL = 'http://localhost:8080'  # Change this to your server's IP/URL

def generate_qrcodes():
    """Generate QR codes for all videos in the database"""

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Connect to database
    if not os.path.exists(DATABASE):
        print(f"Error: Database not found at {DATABASE}")
        print("Please initialize the database first using: python app/init_db.py")
        return

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all videos
    videos = cursor.execute('SELECT id, title, filename FROM videos ORDER BY id').fetchall()

    if not videos:
        print("No videos found in database.")
        print("Add videos using: python app/init_db.py add-video <filename> <title> <keyword> <hint>")
        conn.close()
        return

    print(f"Generating QR codes for {len(videos)} videos...")
    print(f"Base URL: {BASE_URL}")
    print(f"Output directory: {OUTPUT_DIR}/")
    print()

    for video in videos:
        video_id = video['id']
        title = video['title']
        filename = video['filename']

        # Create URL
        url = f"{BASE_URL}/video?id={video_id}"

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save with descriptive filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        output_filename = f"{OUTPUT_DIR}/video_{video_id}_{safe_title}.png"

        img.save(output_filename)
        print(f"✓ Generated: {output_filename}")
        print(f"  Title: {title}")
        print(f"  URL: {url}")
        print()

    conn.close()
    print(f"All QR codes generated in {OUTPUT_DIR}/ directory")
    print("\nPrint these QR codes and place them at the hint locations!")

def print_usage():
    print("Usage:")
    print("  python generate_qrcodes.py [base_url]")
    print()
    print("Examples:")
    print("  python generate_qrcodes.py")
    print("  python generate_qrcodes.py http://192.168.1.100:8080")
    print()
    print("Before running, install requirements:")
    print("  pip install qrcode[pil]")

if __name__ == '__main__':
    # Check if qrcode library is installed
    try:
        import qrcode
    except ImportError:
        print("Error: qrcode library not installed")
        print("Install it with: pip install qrcode[pil]")
        sys.exit(1)

    # Get base URL from command line if provided
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print_usage()
            sys.exit(0)
        BASE_URL = sys.argv[1].rstrip('/')

    generate_qrcodes()
