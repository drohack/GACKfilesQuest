# Video Quest - Complete Setup Guide

This guide will walk you through setting up Video Quest from scratch.

## Prerequisites

Before you begin, ensure you have:

1. **Docker** and **Docker Compose** installed
   - Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - Mac: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - Linux: [Docker Engine](https://docs.docker.com/engine/install/)

2. **Python 3** (for database initialization)
   - Check: `python --version` or `python3 --version`
   - Download: [python.org](https://www.python.org/downloads/)

3. **Video files** in MP4 format

## Step-by-Step Setup

### Step 1: Project Setup

Navigate to the project directory:

```bash
cd GACKfilesQuest-GACKcon2025
```

### Step 2: Initialize the Database

**Option A: Using the initialization script (Recommended)**

```bash
cd app
python init_db.py
cd ..
```

This creates:
- Database with all required tables
- Default admin user (username: `admin`, password: `admin`)
- Three sample video entries

**Option B: Using the quick start script**

Linux/Mac:
```bash
./start.sh
```

Windows:
```bash
start.bat
```

### Step 3: Add Your Videos

1. Place your video files in the `app/videos/` directory:

```bash
# Example
cp ~/Downloads/myvideo.mp4 app/videos/
```

2. Add video entries to the database:

```bash
cd app
python init_db.py add-video myvideo.mp4 "My First Video" "secret123" "Check the bookshelf"
cd ..
```

Parameters:
- **filename**: The actual video file name (must exist in `app/videos/`)
- **title**: Display name shown to users
- **keyword**: Secret word to unlock the video (case-insensitive)
- **hint**: Clue about where to find the QR code

### Step 4: Generate QR Codes

**Option A: Using the provided script**

1. Install QR code library:
```bash
pip install qrcode[pil]
```

2. Generate QR codes:
```bash
python generate_qrcodes.py http://YOUR_SERVER_IP:8080
```

Replace `YOUR_SERVER_IP` with your actual server IP address.

This creates PNG files in the `qrcodes/` directory.

**Option B: Using online generators**

Visit any QR code generator website:
- [QR Code Generator](https://www.qr-code-generator.com/)
- [QR Code Monkey](https://www.qrcode-monkey.com/)

Create QR codes with URLs like:
```
http://YOUR_SERVER_IP:8080/video?id=1
http://YOUR_SERVER_IP:8080/video?id=2
http://YOUR_SERVER_IP:8080/video?id=3
```

### Step 5: Build and Start the Container

```bash
docker-compose up -d
```

This will:
- Build the Docker image (first time only)
- Start the container
- Map port 8080 to your host
- Mount database and videos directory

Check if it's running:
```bash
docker-compose ps
```

View logs:
```bash
docker-compose logs -f
```

### Step 6: Access the Application

1. Open a web browser
2. Navigate to `http://localhost:8080`
3. Login with default credentials:
   - Username: `admin`
   - Password: `admin`

### Step 7: Test the Setup

1. **Test Login**: Ensure you can log in successfully
2. **Test Status Page**: Should show your videos in "Missing" category
3. **Test QR Scanner**: Click "Scan QR Code" and grant camera permissions
4. **Test Video Access**: Navigate directly to `http://localhost:8080/video?id=1`
   - Should mark video as "found"
   - Should show unlock form
5. **Test Unlock**: Enter the correct keyword
   - Should unlock and show the video

### Step 8: Add Additional Users (Optional)

Add more users for multiplayer mode:

```bash
cd app
python init_db.py add-user player1 password123
python init_db.py add-user player2 password456
cd ..
```

### Step 9: Print and Place QR Codes

1. Print the QR code images from the `qrcodes/` directory
2. Place them at the locations described in your hints
3. Test scanning each one with your phone

## Network Access Setup

### Find Your Server IP Address

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

**Mac/Linux:**
```bash
ifconfig
# or
ip addr show
```

### Access from Mobile Device

1. Ensure your phone is on the same WiFi network
2. Open browser on your phone
3. Navigate to: `http://YOUR_SERVER_IP:8080`
4. Login and test the QR scanner

### Firewall Configuration

If you can't access from other devices:

**Windows Firewall:**
```powershell
netsh advfirewall firewall add rule name="Video Quest" dir=in action=allow protocol=TCP localport=8080
```

**Linux (ufw):**
```bash
sudo ufw allow 8080/tcp
```

## Unraid Specific Setup

### Step 1: Create Directory Structure

```bash
mkdir -p /mnt/user/appdata/video-quest
cd /mnt/user/appdata/video-quest
```

### Step 2: Copy Project Files

```bash
# From your computer, copy the entire project
# Using WinSCP, Cyberduck, or command line:
scp -r GACKfilesQuest-GACKcon2025/* root@UNRAID_IP:/mnt/user/appdata/video-quest/
```

### Step 3: Initialize on Unraid

```bash
ssh root@UNRAID_IP
cd /mnt/user/appdata/video-quest/app
python3 init_db.py
cd ..
```

### Step 4: Add Videos

```bash
# Copy videos to Unraid
cp /mnt/user/videos/*.mp4 /mnt/user/appdata/video-quest/app/videos/
```

### Step 5: Start Container

```bash
cd /mnt/user/appdata/video-quest
docker-compose up -d
```

## Verification Checklist

- [ ] Docker container is running (`docker-compose ps`)
- [ ] Database exists (`ls -la app/database.db`)
- [ ] Videos are in place (`ls -la app/videos/`)
- [ ] Can access web interface (`http://localhost:8080`)
- [ ] Can login with default credentials
- [ ] Status page loads and shows videos
- [ ] QR scanner works on mobile device
- [ ] Can scan QR code and mark video as found
- [ ] Can unlock video with correct keyword
- [ ] Video plays successfully

## Common Issues and Solutions

### "Database is locked"
**Solution**: Restart the container
```bash
docker-compose restart
```

### "Cannot access from mobile"
**Solutions**:
1. Verify same WiFi network
2. Check firewall settings
3. Verify IP address is correct
4. Try: `http://IP:8080` not `https://`

### "Camera not working"
**Solutions**:
1. Grant browser camera permissions
2. Try different browser (Chrome recommended)
3. For iOS: Use Safari
4. Check if HTTPS is required (use reverse proxy)

### "Video won't play"
**Solutions**:
1. Verify video format is MP4 with H.264 codec
2. Check file exists in `app/videos/`
3. Verify filename in database matches actual file
4. Check file permissions

### "Port 8080 already in use"
**Solution**: Change port in `docker-compose.yml`
```yaml
ports:
  - "9090:8080"  # Use port 9090 instead
```

## Next Steps

Once everything is working:

1. **Change default password**:
   ```bash
   cd app
   sqlite3 database.db
   # Delete default user and create new one via init_db.py
   ```

2. **Create more videos**: Add more challenges and QR codes

3. **Customize styling**: Edit `app/static/styles.css`

4. **Set up backups**: Regular backups of `app/database.db`

5. **Monitor logs**: Watch for any errors
   ```bash
   docker-compose logs -f
   ```

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify all prerequisites are installed
3. Ensure all files are in the correct locations
4. Review the main README.md for detailed documentation

## Security Reminder

- Change the default password immediately after first login
- This application is designed for LOCAL NETWORK USE ONLY
- Do not expose directly to the internet without proper security measures

Enjoy your Video Quest!
