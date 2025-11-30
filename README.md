# Video Quest - Mobile-Friendly QR Code Video Game

A self-contained Flask web application for running a QR code-based video quest game. Users scan QR codes to discover videos, then unlock them by entering keywords. Perfect for escape rooms, scavenger hunts, or educational games.

## Features

- **QR Code Scanning**: Use device camera to scan QR codes and discover videos
- **Video Hosting**: Locally hosted videos served through Flask
- **Keyword Unlocking**: Videos must be unlocked with correct keywords
- **Progress Tracking**: Track found, unlocked, and missing videos
- **Mobile-Friendly**: Responsive design optimized for phones and tablets
- **Session-Based Authentication**: Secure login with bcrypt password hashing
- **Single Container**: Everything runs in one Docker container
- **Persistent Data**: Database and videos mounted from host

## Tech Stack

- Python 3.11
- Flask web framework
- SQLite database (file-based)
- Jinja2 templates
- html5-qrcode library for QR scanning
- bcrypt for password hashing
- Docker & Docker Compose

## Project Structure

```
.
├── app/
│   ├── app.py                 # Main Flask application
│   ├── init_db.py            # Database initialization script
│   ├── database.db           # SQLite database (created on first run)
│   ├── templates/
│   │   ├── login.html        # Login page
│   │   ├── status.html       # Status/progress page
│   │   ├── qrscan.html       # QR code scanner page
│   │   └── video.html        # Video player and unlock page
│   ├── static/
│   │   ├── styles.css        # Mobile-friendly CSS
│   │   └── qrscanner.js      # QR scanner logic
│   └── videos/               # Video files directory (mounted)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Clone or Download This Project

```bash
git clone <repository-url>
cd GACKfilesQuest-GACKcon2025
```

### 2. Initialize the Database

Before starting the container, initialize the database with default user and sample videos:

```bash
cd app
python init_db.py
```

This creates:
- Database tables
- Default user (username: `admin`, password: `admin`)
- Three sample video entries

**Important**: Change the default password after first login!

### 3. Add Your Videos

Place your video files (MP4 format recommended) in the `app/videos/` directory:

```bash
cp /path/to/your/video1.mp4 app/videos/
cp /path/to/your/video2.mp4 app/videos/
```

Make sure the filenames match those in the database.

### 4. Build and Run the Container

```bash
docker-compose up -d
```

This will:
- Build the Docker image
- Start the container
- Mount the database and videos directory
- Expose the application on port 8080

### 5. Access the Application

Open a web browser and navigate to:

```
http://localhost:8080
```

Or from another device on the same network:

```
http://<server-ip>:8080
```

Login with:
- **Username**: admin
- **Password**: admin

## Usage Guide

### Login Flow

1. Navigate to the application URL
2. Enter username and password
3. Click "Login"
4. Redirected to Status page on success

### Status Page

Shows three categories of videos:

- **Unlocked Videos**: Videos you've found and unlocked (green)
- **Found Videos**: Videos you've scanned but not unlocked yet (yellow)
- **Missing Videos**: Videos you haven't found yet, with hints (gray)

Buttons:
- **Scan QR Code**: Opens the QR scanner
- **Logout**: Ends your session

### Scanning QR Codes

1. Click "Scan QR Code" from the Status page
2. Grant camera permissions when prompted
3. Point camera at a QR code
4. When recognized, automatically redirects to the video page

QR codes should contain:
- Full URL: `http://your-server:8080/video?id=1`
- Relative URL: `/video?id=1`
- Just the ID: `1`

### Video Page

When you visit a video (by scanning or clicking from Status):

**If Not Unlocked:**
- Shows a locked icon
- Displays an unlock form
- Enter the correct keyword to unlock
- Video automatically marks as "found"

**If Unlocked:**
- Shows success banner
- Video player displays with controls
- Can watch the video

### Unlocking Videos

1. Navigate to a found video
2. Enter the keyword in the unlock form
3. Click "Unlock Video"
4. If correct: video unlocks and page reloads
5. If incorrect: error message displays

Keywords are case-insensitive.

## Database Management

### Add a New User

```bash
cd app
python init_db.py add-user <username> <password>
```

Example:
```bash
python init_db.py add-user player1 secretpass123
```

### Add a New Video

```bash
cd app
python init_db.py add-video <filename> <title> <keyword> [hint]
```

Example:
```bash
python init_db.py add-video challenge1.mp4 "First Challenge" "secret123" "Look behind the painting"
```

### Direct Database Access

Use SQLite command-line tool or any SQLite browser:

```bash
sqlite3 app/database.db
```

Useful queries:

```sql
-- View all users
SELECT * FROM users;

-- View all videos
SELECT * FROM videos;

-- View user progress
SELECT u.username, v.title, f.found_at, ul.unlocked_at
FROM users u
LEFT JOIN found f ON u.id = f.user_id
LEFT JOIN videos v ON f.video_id = v.id
LEFT JOIN unlocks ul ON u.id = ul.user_id AND v.id = ul.video_id;

-- Reset a user's progress
DELETE FROM found WHERE user_id = 1;
DELETE FROM unlocks WHERE user_id = 1;
```

## Creating QR Codes

You can create QR codes using any QR code generator. The QR code should contain one of:

1. **Full URL**: `http://192.168.1.100:8080/video?id=1`
2. **Relative URL**: `/video?id=1`
3. **Just the ID**: `1`

### Online QR Code Generators

- [QR Code Generator](https://www.qr-code-generator.com/)
- [QR Code Monkey](https://www.qrcode-monkey.com/)
- [goQR.me](https://goqr.me/)

### Command-Line QR Code Generation

Using `qrencode`:

```bash
# Install qrencode
sudo apt-get install qrencode  # Debian/Ubuntu
brew install qrencode           # macOS

# Generate QR code
qrencode -o video1-qr.png "http://192.168.1.100:8080/video?id=1"
```

## Docker Management

### View Logs

```bash
docker-compose logs -f
```

### Restart Container

```bash
docker-compose restart
```

### Stop Container

```bash
docker-compose down
```

### Rebuild After Changes

```bash
docker-compose up -d --build
```

### Access Container Shell

```bash
docker exec -it video-quest /bin/bash
```

## Deployment on Unraid

1. **Create Directories**:
   ```bash
   mkdir -p /mnt/user/appdata/video-quest/app/videos
   ```

2. **Copy Files**:
   ```bash
   # Copy all project files to Unraid
   cp -r GACKfilesQuest-GACKcon2025/* /mnt/user/appdata/video-quest/
   ```

3. **Initialize Database**:
   ```bash
   cd /mnt/user/appdata/video-quest/app
   python init_db.py
   ```

4. **Add Videos**:
   ```bash
   cp /path/to/videos/*.mp4 /mnt/user/appdata/video-quest/app/videos/
   ```

5. **Update docker-compose.yml** (if needed):
   ```yaml
   volumes:
     - /mnt/user/appdata/video-quest/app/database.db:/app/database.db
     - /mnt/user/appdata/video-quest/app/videos:/app/videos
   ```

6. **Start Container**:
   ```bash
   cd /mnt/user/appdata/video-quest
   docker-compose up -d
   ```

## Configuration

### Change Port

Edit `docker-compose.yml`:

```yaml
ports:
  - "9090:8080"  # Change left number (host port)
```

### Session Expiry

Edit `app/app.py`:

```python
app.config['SESSION_EXPIRY_HOURS'] = 48  # Change from 24 to 48 hours
```

### Video Upload Limits

By default, Flask has a 16MB upload limit. To serve larger videos, they should be pre-loaded into the videos directory rather than uploaded through the app.

## Security Considerations

### For LAN-Only Use

This application is designed for local network use only:

- Cookies use `Secure=False` (no HTTPS required)
- Default credentials should be changed
- No rate limiting on login attempts
- Session tokens stored in database

### If Exposing to Internet

**Not recommended**, but if you must:

1. Use a reverse proxy with HTTPS (nginx, Caddy)
2. Set `Secure=True` for cookies
3. Add rate limiting
4. Use strong passwords
5. Consider adding CAPTCHA to login
6. Enable CORS protection

## Troubleshooting

### Camera Not Working

- **Check Permissions**: Ensure browser has camera access
- **HTTPS Required**: Some browsers require HTTPS for camera access
  - Use a reverse proxy with SSL
  - Or add exception for local IP
- **Try Different Browser**: Chrome/Safari have better camera support

### Videos Won't Play

- **Check Format**: Use MP4 with H.264 codec
- **Check File Location**: Ensure videos are in `app/videos/` directory
- **Check Permissions**: Container must have read access
- **Check Filename**: Must match database entry exactly

### Database Locked Error

- Only one connection can write at a time
- Usually resolves itself
- If persistent, restart container:
  ```bash
  docker-compose restart
  ```

### Port Already in Use

Change the host port in `docker-compose.yml`:

```yaml
ports:
  - "8081:8080"
```

### Container Won't Start

Check logs:
```bash
docker-compose logs
```

Common issues:
- Database file permissions
- Videos directory missing
- Port conflict
- Python dependency issues

## Backup and Restore

### Backup Database

```bash
cp app/database.db app/database.db.backup
```

Or use SQLite dump:

```bash
sqlite3 app/database.db .dump > backup.sql
```

### Restore Database

```bash
cp app/database.db.backup app/database.db
```

Or from SQL dump:

```bash
sqlite3 app/database.db < backup.sql
```

### Backup Videos

```bash
tar -czf videos-backup.tar.gz app/videos/
```

## License

This project is provided as-is for educational and entertainment purposes.

## Support

For issues, questions, or contributions, please open an issue on the project repository.
