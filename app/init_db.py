#!/usr/bin/env python3
"""
Database initialization script
Run this to create a new database with sample data
"""
import sqlite3
import bcrypt
import sys

DATABASE = 'database.db'

def init_database():
    """Initialize database with tables and sample data"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
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
            hint TEXT
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

    # Add default user (username: admin, password: admin)
    password_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      ('admin', password_hash))
        print("[OK] Default user created (username: admin, password: admin)")
    except sqlite3.IntegrityError:
        print("[!] Default user already exists")

    # Add sample videos - one for each cryptid body part
    sample_videos = [
        ('head.mp4', 'HEAD', 'cranium', 'Scan the highest point of the location'),
        ('claws.mp4', 'CLAWS', 'talons', 'Look for evidence near the entrance'),
        ('body.mp4', 'BODY', 'torso', 'Search the central area'),
        ('feet.mp4', 'FEET', 'limbs', 'Check near the ground level'),
        ('tail.mp4', 'TAIL', 'appendage', 'Investigate the rear section'),
    ]

    for filename, title, keyword, hint in sample_videos:
        try:
            cursor.execute('INSERT INTO videos (filename, title, keyword, hint) VALUES (?, ?, ?, ?)',
                          (filename, title, keyword, hint))
            print(f"[OK] Added video: {title}")
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

def add_video(filename, title, keyword, hint=''):
    """Add a new video to the database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO videos (filename, title, keyword, hint) VALUES (?, ?, ?, ?)',
                      (filename, title, keyword, hint))
        conn.commit()
        print(f"[OK] Video '{title}' added successfully!")
    except sqlite3.IntegrityError:
        print(f"[X] Video with this filename already exists!")
    finally:
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'add-user' and len(sys.argv) == 4:
            add_user(sys.argv[2], sys.argv[3])
        elif command == 'add-video' and len(sys.argv) >= 5:
            hint = sys.argv[5] if len(sys.argv) > 5 else ''
            add_video(sys.argv[2], sys.argv[3], sys.argv[4], hint)
        else:
            print("Usage:")
            print("  python init_db.py                                    # Initialize database")
            print("  python init_db.py add-user <username> <password>    # Add a user")
            print("  python init_db.py add-video <filename> <title> <keyword> [hint]  # Add a video")
    else:
        init_database()
