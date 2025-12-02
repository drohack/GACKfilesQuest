#!/usr/bin/env python3
"""
Database initialization script
Run this to create a new database with sample data
"""
import sqlite3
import bcrypt
import sys

DATABASE = 'database.db'

def migrate_database():
    """Update existing database schema without losing data"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("Checking for database updates...")

    # Check users table columns
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [column[1] for column in cursor.fetchall()]

    if 'seen_intro' not in user_columns:
        print("Adding seen_intro column to users table...")
        cursor.execute('ALTER TABLE users ADD COLUMN seen_intro INTEGER DEFAULT 0')
        print("[OK] Added seen_intro column")

    if 'is_admin' not in user_columns:
        print("Adding is_admin column to users table...")
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
        print("[OK] Added is_admin column")

    # Check videos table columns
    cursor.execute("PRAGMA table_info(videos)")
    video_columns = [column[1] for column in cursor.fetchall()]

    if 'scan_code' not in video_columns:
        print("Adding scan_code column to videos table...")
        try:
            cursor.execute('ALTER TABLE videos ADD COLUMN scan_code TEXT')
            print("[OK] Added scan_code column")
            print("[!] WARNING: Existing videos need scan codes added via admin panel or CLI")
        except sqlite3.OperationalError as e:
            print(f"[!] Could not add scan_code: {e}")

    conn.commit()
    conn.close()
    print("Database migration complete!\n")

def init_database():
    """Initialize database with tables and sample data"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            seen_intro INTEGER DEFAULT 0
        )
    ''')

    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            title TEXT NOT NULL,
            keyword TEXT NOT NULL,
            hint TEXT,
            scan_code TEXT UNIQUE NOT NULL
        )
    ''')

    # Create found table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS found (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (video_id) REFERENCES videos(id),
            UNIQUE(user_id, video_id)
        )
    ''')

    # Create unlocks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unlocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            video_id INTEGER NOT NULL,
            unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (video_id) REFERENCES videos(id),
            UNIQUE(user_id, video_id)
        )
    ''')

    print("[OK] Database tables created")

    # Add default admin user (username: admin, password: admin)
    password_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                      ('admin', password_hash, 1))
        print("[OK] Default admin user created (username: admin, password: admin)")
    except sqlite3.IntegrityError:
        print("[!] Default user already exists")

    # Add sample videos - one for each cryptid body part
    # Format: (filename, title, keyword, hint, scan_code)
    sample_videos = [
        ('head.mp4', 'HEAD', 'cranium', 'Scan the highest point of the location', 'GACK_HEAD_7X9K2'),
        ('claws.mp4', 'CLAWS', 'talons', 'Look for evidence near the entrance', 'GACK_CLAW_4M8N1'),
        ('body.mp4', 'BODY', 'torso', 'Search the central area', 'GACK_BODY_3P5L6'),
        ('feet.mp4', 'FEET', 'limbs', 'Check near the ground level', 'GACK_FEET_9R2T4'),
        ('tail.mp4', 'TAIL', 'appendage', 'Investigate the rear section', 'GACK_TAIL_6Q1W8'),
    ]

    for filename, title, keyword, hint, scan_code in sample_videos:
        try:
            cursor.execute('INSERT INTO videos (filename, title, keyword, hint, scan_code) VALUES (?, ?, ?, ?, ?)',
                          (filename, title, keyword, hint, scan_code))
            print(f"[OK] Added video: {title} (scan code: {scan_code})")
        except sqlite3.IntegrityError:
            print(f"[!] Video already exists: {title}")

    conn.commit()
    conn.close()
    print("\nDatabase initialized successfully!")
    print("\nDefault credentials:")
    print("  Username: admin")
    print("  Password: admin")
    print("\nRemember to change the default password!")

def add_user(username, password):
    """Add a new user to the database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      (username, password_hash))
        conn.commit()
        print(f"[OK] User '{username}' created successfully!")
    except sqlite3.IntegrityError:
        print(f"[X] User '{username}' already exists!")
    finally:
        conn.close()

def add_video(filename, title, keyword, scan_code, hint=''):
    """Add a new video to the database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO videos (filename, title, keyword, hint, scan_code) VALUES (?, ?, ?, ?, ?)',
                      (filename, title, keyword, hint, scan_code))
        conn.commit()
        print(f"[OK] Video '{title}' added successfully!")
        print(f"  Scan code: {scan_code}")
    except sqlite3.IntegrityError:
        print(f"[X] Video already exists or scan code is not unique!")
    finally:
        conn.close()

def edit_video(video_id, title=None, keyword=None, hint=None, scan_code=None, filename=None):
    """Edit an existing video"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get current video
    video = cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()
    if not video:
        print(f"[X] Video ID {video_id} not found!")
        conn.close()
        return

    # Use existing values if not provided
    new_filename = filename if filename else video[1]
    new_title = title if title else video[2]
    new_keyword = keyword if keyword else video[3]
    new_hint = hint if hint else video[4]
    new_scan_code = scan_code if scan_code else video[5]

    try:
        cursor.execute('''UPDATE videos
                         SET filename = ?, title = ?, keyword = ?, hint = ?, scan_code = ?
                         WHERE id = ?''',
                       (new_filename, new_title, new_keyword, new_hint, new_scan_code, video_id))
        conn.commit()
        print(f"[OK] Video ID {video_id} updated successfully!")
        print(f"  Title: {new_title}")
        print(f"  Scan Code: {new_scan_code}")
        print(f"  Keyword: {new_keyword}")
    except sqlite3.IntegrityError:
        print(f"[X] Update failed! Scan code must be unique.")
    finally:
        conn.close()

def reset_password(username, new_password):
    """Reset a user's password"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if user exists
    user = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        print(f"[X] User '{username}' not found!")
        conn.close()
        return

    # Hash new password
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    # Update password
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?',
                   (password_hash, username))
    conn.commit()
    conn.close()
    print(f"[OK] Password reset for user '{username}'!")

def list_videos():
    """List all videos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    videos = cursor.execute('SELECT * FROM videos ORDER BY id').fetchall()
    conn.close()

    if not videos:
        print("No videos found.")
        return

    print("\n=== Videos ===")
    for video in videos:
        print(f"\nID: {video['id']}")
        print(f"  Title: {video['title']}")
        print(f"  Scan Code: {video['scan_code']}")
        print(f"  Keyword: {video['keyword']}")
        print(f"  Hint: {video['hint']}")
        print(f"  Filename: {video['filename']}")

def list_users():
    """List all users"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    users = cursor.execute('SELECT id, username FROM users ORDER BY id').fetchall()
    conn.close()

    if not users:
        print("No users found.")
        return

    print("\n=== Users ===")
    for user in users:
        print(f"ID: {user['id']}, Username: {user['username']}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'add-user' and len(sys.argv) == 4:
            add_user(sys.argv[2], sys.argv[3])
        elif command == 'add-video' and len(sys.argv) >= 6:
            hint = sys.argv[6] if len(sys.argv) > 6 else ''
            add_video(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], hint)
        elif command == 'edit-video' and len(sys.argv) >= 3:
            video_id = int(sys.argv[2])
            # Parse optional arguments
            title = sys.argv[3] if len(sys.argv) > 3 else None
            keyword = sys.argv[4] if len(sys.argv) > 4 else None
            hint = sys.argv[5] if len(sys.argv) > 5 else None
            scan_code = sys.argv[6] if len(sys.argv) > 6 else None
            filename = sys.argv[7] if len(sys.argv) > 7 else None
            edit_video(video_id, title, keyword, hint, scan_code, filename)
        elif command == 'reset-password' and len(sys.argv) == 4:
            reset_password(sys.argv[2], sys.argv[3])
        elif command == 'list-videos':
            list_videos()
        elif command == 'list-users':
            list_users()
        elif command == 'migrate':
            migrate_database()
        else:
            print("Usage:")
            print("  python init_db.py                                                     # Initialize database")
            print("  python init_db.py migrate                                             # Update database schema (keeps data)")
            print("  python init_db.py add-user <username> <password>                     # Add a user")
            print("  python init_db.py add-video <filename> <title> <keyword> <scan_code> [hint]  # Add a video")
            print("  python init_db.py edit-video <id> [title] [keyword] [hint] [scan_code] [filename]  # Edit a video")
            print("  python init_db.py reset-password <username> <new_password>           # Reset user password")
            print("  python init_db.py list-videos                                        # List all videos")
            print("  python init_db.py list-users                                         # List all users")
            print("\nExamples:")
            print("  python init_db.py add-video head.mp4 HEAD cranium GACK_HEAD_X1Y2    # Add new video")
            print("  python init_db.py edit-video 1 'Skull Fragment' bones               # Update title and keyword")
            print("  python init_db.py edit-video 3 '' '' 'New hint' GACK_NEW_CODE       # Update hint and scan code")
            print("  python init_db.py reset-password admin newpass123                   # Reset admin password")
    else:
        init_database()
