# GACKfiles Quest - X-Files Themed Cryptid Investigation Game

A mobile-friendly Flask web application for running an X-Files inspired cryptid hunting experience. Agents scan evidence markers (QR codes) to discover video clues, analyze evidence, and solve cases. Features anti-sharing security, dark themed UI, and complete admin panel.

## Features

- **Secure QR Code System**: Static QR codes contain unique scan codes (not URLs) - prevents URL sharing
- **Anti-Cheating Protection**: Users must physically scan QR codes to access videos
- **X-Files Theme**: Dark, mysterious interface with green glow effects and cryptid silhouette
- **Cryptid Anatomy Diagram**: Visual investigation board with body part evidence markers
- **Web Admin Panel**: Manage all evidence and agents through browser interface
- **CLI Admin Tools**: Command-line scripts for SSH management
- **Video Hosting**: Locally hosted videos served through Flask
- **Case Solving**: Watch evidence videos and enter solution codes
- **Progress Tracking**: Visual cryptid diagram shows solved/found/undiscovered evidence
- **Mobile-Optimized**: Responsive dark theme with touch-friendly controls
- **HTTPS Support**: SSL certificate support for mobile camera access
- **Session Authentication**: Secure login with bcrypt password hashing
- **Single Container**: Everything runs in one Docker container
- **Persistent Data**: Database and videos mounted from host

## Tech Stack

- Python 3.11 + Flask
- SQLite database (file-based)
- Jinja2 templates
- html5-qrcode library for QR scanning
- bcrypt for password hashing
- Docker & Docker Compose
- HTTPS with self-signed certificates

## Theme

**X-Files / Cryptid Hunter Aesthetic:**
- Dark background with Matrix-green (#00ff41) accents
- Courier New monospace font (government document style)
- "CLASSIFIED" watermarks and glowing text effects
- Paranormal investigation terminology
- "The Truth Is Out There" tagline

## Quick Start

### 1. Initialize the Database

```bash
cd app
python init_db.py
```

Creates:
- Database with all tables
- Admin user (username: `admin`, password: `admin`, is_admin: 1)
- 5 cryptid body part evidence videos with scan codes

### 2. Add Your Videos

```bash
cp /path/to/videos/*.mp4 app/videos/
```

Filename must match database entries:
- head.mp4, claws.mp4, body.mp4, feet.mp4, tail.mp4

### 3. Start the Container

```bash
docker-compose up -d
```

### 4. Access the Application

**Main Site:** `http://YOUR_IP:57823`

**Login:** admin / admin

**Note:** For HTTPS access and public internet exposure, use a reverse proxy like Nginx Proxy Manager.

## How It Works

### Security Model (Anti-Sharing)

**QR Codes Contain:** Just scan codes (e.g., `GACK_HEAD_7X9K2`) - NOT URLs

**Scanning Process:**
1. User scans QR code with in-app scanner
2. Third-party scanners show meaningless text (useless)
3. In-app scanner sends code to server via `/verify-scan`
4. Server validates code and marks video as "found" for that user
5. Server returns video ID
6. User redirects to `/video?id=1`

**Sharing Prevention:**
- Direct video URL access checks if user has "found" the video
- If not found: Shows "NO CHEATING" error page
- If found: Shows video and case analysis form
- Users MUST scan QR codes themselves - can't share URLs

**Result:** Static QR codes, but URL sharing doesn't work!

### Game Flow

1. **Login** → Agent Access Portal
2. **Field Reports** → Visual cryptid diagram with 5 body parts
3. **Scan Evidence** → Camera scanner reads QR codes
4. **Investigate** → Watch evidence video
5. **Submit Solution** → Enter keyword to solve case
6. **Case Closed** → Evidence marked as solved

### Cryptid Anatomy Diagram

Central cryptid silhouette with 5 evidence markers:
- **HEAD** (top) - connects to head
- **CLAWS** (left, top) - connects to claws
- **TAIL** (left, bottom) - connects to tail
- **BODY** (right) - connects to torso
- **FEET** (bottom) - connects to feet

Each marker shows:
- Status icon (?, 📂, or ✓)
- Title
- Found/Solved status
- Investigate/Review button (when found)
- Hint text (when not found)

Connecting lines point from markers to body parts with color coding:
- Gray: Not found
- Orange: Found but not solved
- Green: Solved

## Admin Panel

**Access:** `https://YOUR_IP:57823/admin` (admin users only)

### Evidence Management
- View all videos in table format
- Edit titles, keywords, hints, scan codes, filenames
- Inline editing forms
- Real-time updates

### Agent Management
- View all users with admin status
- Reset any user's password
- Compact mobile-friendly table

### Features
- Click "Edit" to expand inline form
- Changes apply immediately
- Success/error messages
- No container restart needed

## Database Management

All commands run from the `app/` directory. Changes apply instantly - just refresh browser!

### List Everything

```bash
cd app
python init_db.py list-videos    # Shows all videos with scan codes
python init_db.py list-users     # Shows all users with admin status
```

### Add New Video

```bash
python init_db.py add-video <filename> <title> <keyword> <scan_code> [hint]
```

Example:
```bash
python init_db.py add-video skull.mp4 "SKULL" bones GACK_SKULL_X9Z2 "Check the basement"
```

### Edit Video

```bash
python init_db.py edit-video <id> [title] [keyword] [hint] [scan_code] [filename]
```

Examples:
```bash
# Edit just the title
python init_db.py edit-video 1 "Skull Fragment"

# Edit title and keyword
python init_db.py edit-video 2 "Claw Marks" sharptalons

# Edit hint and scan code
python init_db.py edit-video 3 '' '' 'New hint' GACK_NEW_CODE

# Edit everything
python init_db.py edit-video 4 "Foot Print" tracks "Found outside" GACK_FEET_NEW foot.mp4
```

**Use empty strings (`''`) to skip fields you don't want to change.**

### Reset User Password

```bash
python init_db.py reset-password <username> <new_password>
```

Examples:
```bash
python init_db.py reset-password admin mynewpass
python init_db.py reset-password player1 resetpass123
```

### Add New User

```bash
python init_db.py add-user <username> <password>
```

Example:
```bash
python init_db.py add-user player2 secretpass
```

**Note:** New users are NOT admins by default. Use SQL to set `is_admin=1` if needed.

## Creating QR Codes

QR codes must contain only the scan code (not URLs)!

### Current Scan Codes

- **HEAD**: `GACK_HEAD_7X9K2`
- **CLAWS**: `GACK_CLAW_4M8N1`
- **BODY**: `GACK_BODY_3P5L6`
- **FEET**: `GACK_FEET_9R2T4`
- **TAIL**: `GACK_TAIL_6Q1W8`

### Generate QR Codes

Use any QR code generator with **just the scan code as text**:

**Online Generators:**
- [QR Code Generator](https://www.qr-code-generator.com/)
- [QR Code Monkey](https://www.qrcode-monkey.com/)

**Enter:** `GACK_HEAD_7X9K2` (not a URL!)

**Command Line:**
```bash
# Install qrencode
sudo apt-get install qrencode  # Linux
brew install qrencode           # Mac

# Generate QR codes
qrencode -o head-qr.png "GACK_HEAD_7X9K2"
qrencode -o claws-qr.png "GACK_CLAW_4M8N1"
qrencode -o body-qr.png "GACK_BODY_3P5L6"
qrencode -o feet-qr.png "GACK_FEET_9R2T4"
qrencode -o tail-qr.png "GACK_TAIL_6Q1W8"
```

**Important:** Third-party QR scanners will show useless text. Only the in-app scanner validates codes with the server!

## Security Features

### Anti-Sharing System

**Problem Solved:** Users can't share video URLs to bypass QR code hunting.

**How It Works:**
1. QR codes contain scan codes, not URLs
2. Must use in-app scanner (third-party scanners are useless)
3. Server validates code and marks as "found"
4. Direct video URL access checks "found" status
5. No found record = "NO CHEATING" error page

**Benefits:**
- Static QR codes (never change)
- Can't bypass by sharing URLs
- Must physically find and scan each QR code
- Tracks legitimate discoveries per user

### Admin Access Control

- `is_admin` field in users table
- Admin-only routes protected by `@admin_required` decorator
- Non-admins get 403 error
- Default admin user created during init

## Configuration

### Change Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "9090:8080"  # Change 57823 to desired port
```

### Session Expiry

Edit `app/app.py`:
```python
app.config['SESSION_EXPIRY_HOURS'] = 48  # Default is 24
```

### Customize Scan Codes

Edit codes in admin panel or via CLI:
```bash
python app/init_db.py edit-video 1 '' '' '' CUSTOM_CODE_HERE
```

Scan codes must be unique!

## Docker Management

```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Access container shell
docker exec -it video-quest /bin/bash
```

## Updating the Application

### Update on Unraid (Preserves Database)

Pull latest changes from GitHub and rebuild while keeping all user data:

```bash
# SSH into Unraid
ssh root@YOUR_UNRAID_IP

# Navigate to app directory
cd /mnt/user/appdata/gackfiles-quest

# Pull latest code from GitHub
git pull

# Rebuild and restart container
docker-compose down
docker-compose up -d --build

# Verify it's running
docker-compose logs --tail 20
```

**Your data is safe!** The update only affects code files:
- `app/database.db` is preserved (in .gitignore)
- All user accounts, progress, and settings remain intact
- Video files stay in place
- Same login credentials

**After update:** Access at your normal URL with existing credentials.

### Update Locally (Development)

```bash
# Pull latest changes
git pull

# Rebuild container
docker-compose down
docker-compose up -d --build
```

## Deployment on Unraid

### Setup

1. Create directory:
```bash
mkdir -p /mnt/user/appdata/gackfiles-quest
```

2. Copy project files:
```bash
scp -r GACKfilesQuest-GACKcon2025/* root@UNRAID_IP:/mnt/user/appdata/gackfiles-quest/
```

3. Initialize database:
```bash
ssh root@UNRAID_IP
cd /mnt/user/appdata/gackfiles-quest

# Create empty database file
touch app/database.db
chmod 666 app/database.db

# Start container
docker-compose up -d

# Initialize database inside container
docker exec -it video-quest python init_db.py
```

4. Add videos:
```bash
cp /mnt/user/videos/*.mp4 /mnt/user/appdata/gackfiles-quest/app/videos/
```

### Access

**Internal (LAN):**
```
http://UNRAID_IP:57823
```

**External (Internet):**
Set up Nginx Proxy Manager to handle SSL and domain routing. The app runs on HTTP internally, NPM provides HTTPS externally.

## Reverse Proxy Setup (Nginx Proxy Manager)

For public internet access with proper SSL:

**In NPM:**
- **Scheme:** http
- **Forward Hostname/IP:** Your Unraid/server IP (e.g., 192.168.1.2)
- **Forward Port:** 57823
- **SSL:** Request Let's Encrypt certificate
- **Force SSL:** Enabled
- **Websockets:** Enabled

**Domain DNS:** Point your domain A record to your public IP in your DNS provider.

**Router:** Forward ports 80 and 443 to your NPM server.

That's it! NPM handles SSL termination, the app serves HTTP internally.

## Troubleshooting

### Camera Not Working

**Issue:** "Unable to access camera" on mobile

**Solutions:**
1. Ensure accessing via HTTPS (use reverse proxy like NPM)
2. Grant camera permissions when prompted
3. Try Chrome/Safari (best camera API support)
4. Check that you're using a valid SSL certificate (Let's Encrypt via NPM)
5. Mobile browsers require HTTPS for camera access

### "NO CHEATING" Error Page

**Issue:** Can't access video even though you scanned it

**Solutions:**
1. Make sure you scanned with the in-app scanner (not third-party)
2. Check if scan was successful ("Evidence discovered!")
3. Verify you're logged in as the correct user
4. Try scanning again

### Videos Won't Play

**Solutions:**
1. Verify video files exist in `app/videos/`
2. Check filenames match database exactly
3. Use MP4 format with H.264 codec
4. Check file permissions
5. View browser console for errors

### Admin Panel Shows 403 Error

**Solution:** Login as admin user (is_admin=1)

To check admin status:
```bash
sqlite3 app/database.db
SELECT username, is_admin FROM users;
```

To make user admin:
```bash
sqlite3 app/database.db
UPDATE users SET is_admin=1 WHERE username='admin';
```

### Database Locked Error

**Solution:** Restart container
```bash
docker-compose restart
```

### Port Already in Use

**Solution:** Change port in docker-compose.yml
```yaml
ports:
  - "8080:8080"  # Change left number
```

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
docker-compose restart
```

### Reset User Progress

```bash
sqlite3 app/database.db
DELETE FROM found WHERE user_id = 1;
DELETE FROM unlocks WHERE user_id = 1;
```

## Database Schema

### Tables

**users**
- id, username, password_hash, is_admin

**sessions**
- token, user_id, expires_at

**videos**
- id, filename, title, keyword, hint, scan_code

**found**
- id, user_id, video_id, found_at

**unlocks**
- id, user_id, video_id, unlocked_at

## Advanced Usage

### Direct Database Access

```bash
sqlite3 app/database.db
```

Useful queries:
```sql
-- View all scan codes
SELECT id, title, scan_code FROM videos;

-- View user progress
SELECT u.username, v.title, f.found_at, ul.unlocked_at
FROM users u
LEFT JOIN found f ON u.id = f.user_id
LEFT JOIN videos v ON f.video_id = v.id
LEFT JOIN unlocks ul ON u.id = ul.user_id AND v.id = ul.video_id;

-- Reset all progress
DELETE FROM found;
DELETE FROM unlocks;

-- Make user admin
UPDATE users SET is_admin=1 WHERE username='player1';
```

### Custom Scan Codes

Generate unique codes for your QR codes:
```bash
# Random alphanumeric
echo "GACK_$(head /dev/urandom | tr -dc A-Z0-9 | head -c 10)"
# Example output: GACK_X7K9M2P4L1
```

Then update via admin panel or CLI:
```bash
python init_db.py edit-video 1 '' '' '' GACK_CUSTOM_CODE
```

## Terminology Reference

| Old Term | GACKfiles Term |
|----------|----------------|
| Video Quest | GACKfiles |
| Status Page | Field Reports |
| Videos | Evidence Files |
| Challenges | Cases |
| QR Code | Evidence Marker |
| Unlock | Solve Case |
| Found | Discovered |
| Completed | Solved |
| Keyword | Solution Code |
| Login | Agent Access Portal |
| Username | Agent ID |

## File Structure

```
GACKfilesQuest-GACKcon2025/
├── app/
│   ├── app.py                    # Main Flask application
│   ├── init_db.py               # Database initialization & CLI tools
│   ├── database.db              # SQLite database (mounted)
│   ├── templates/
│   │   ├── login.html           # Agent access portal
│   │   ├── status.html          # Cryptid diagram & field reports
│   │   ├── qrscan.html          # Evidence scanner
│   │   ├── video.html           # Evidence viewer & case analysis
│   │   ├── admin.html           # Admin management panel
│   │   └── no_access.html       # Anti-cheating error page
│   ├── static/
│   │   ├── styles.css           # X-Files dark theme
│   │   └── qrscanner.js         # QR scanner logic
│   └── videos/                  # Video files directory (mounted)
├── Dockerfile                   # Container build configuration
├── docker-compose.yml           # Port 57823, volume mounts
├── requirements.txt             # Python dependencies
├── README.md                    # Complete documentation
├── start.sh / start.bat        # Quick start scripts
├── .gitignore                   # Git exclusions
└── .env.example                 # Environment variables template
```

## Current Evidence (Default)

| Body Part | Scan Code | Keyword | Video File |
|-----------|-----------|---------|------------|
| HEAD | GACK_HEAD_7X9K2 | cranium | head.mp4 |
| CLAWS | GACK_CLAW_4M8N1 | talons | claws.mp4 |
| BODY | GACK_BODY_3P5L6 | torso | body.mp4 |
| FEET | GACK_FEET_9R2T4 | limbs | feet.mp4 |
| TAIL | GACK_TAIL_6Q1W8 | appendage | tail.mp4 |

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review database management commands
- Check Docker logs: `docker-compose logs`

## License

Provided as-is for educational and entertainment purposes.

---

**"The Truth Is Out There... But You Have To Find It Yourself"**
