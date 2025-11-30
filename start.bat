@echo off
REM Quick start script for Video Quest (Windows)

echo ====================================
echo   Video Quest - Quick Start Script
echo ====================================
echo.

REM Check if database exists
if not exist "app\database.db" (
    echo Database not found. Initializing...
    cd app
    python init_db.py
    cd ..
    echo.
) else (
    echo Database already exists.
    echo.
)

REM Check if videos directory has content
dir /b "app\videos\*.mp4" >nul 2>&1
if errorlevel 1 (
    echo Warning: No video files found in app\videos\
    echo Please add your .mp4 files to the app\videos\ directory
    echo.
)

echo Starting Docker container...
docker-compose up -d

echo.
echo ====================================
echo Video Quest is starting!
echo ====================================
echo.
echo Access the application at:
echo   http://localhost:8080
echo.
echo Default credentials:
echo   Username: admin
echo   Password: admin
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop:
echo   docker-compose down
echo.

pause
