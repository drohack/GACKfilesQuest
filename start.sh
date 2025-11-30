#!/bin/bash
# Quick start script for Video Quest

echo "===================================="
echo "  Video Quest - Quick Start Script"
echo "===================================="
echo ""

# Check if database exists
if [ ! -f "app/database.db" ]; then
    echo "Database not found. Initializing..."
    cd app
    python3 init_db.py
    cd ..
    echo ""
else
    echo "Database already exists."
    echo ""
fi

# Check if videos directory has content
VIDEO_COUNT=$(ls -1 app/videos/*.mp4 2>/dev/null | wc -l)
if [ "$VIDEO_COUNT" -eq 0 ]; then
    echo "Warning: No video files found in app/videos/"
    echo "Please add your .mp4 files to the app/videos/ directory"
    echo ""
fi

echo "Starting Docker container..."
docker-compose up -d

echo ""
echo "===================================="
echo "Video Quest is starting!"
echo "===================================="
echo ""
echo "Access the application at:"
echo "  http://localhost:8080"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
