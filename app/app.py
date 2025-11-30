import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory, jsonify
import bcrypt

app = Flask(__name__)
app.config['DATABASE'] = 'database.db'
app.config['VIDEO_FOLDER'] = 'videos'
app.config['SESSION_EXPIRY_HOURS'] = 24

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
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

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# Authentication helpers
def create_session(user_id):
    """Create a new session token for a user"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=app.config['SESSION_EXPIRY_HOURS'])

    conn = get_db_connection()
    conn.execute('INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)',
                 (token, user_id, expires_at))
    conn.commit()
    conn.close()

    return token

def get_user_from_session(token):
    """Get user ID from session token if valid"""
    if not token:
        return None

    conn = get_db_connection()
    session = conn.execute(
        'SELECT user_id FROM sessions WHERE token = ? AND expires_at > ?',
        (token, datetime.now())
    ).fetchone()
    conn.close()

    return session['user_id'] if session else None

def delete_session(token):
    """Delete a session token"""
    conn = get_db_connection()
    conn.execute('DELETE FROM sessions WHERE token = ?', (token,))
    conn.commit()
    conn.close()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('session')
        user_id = get_user_from_session(token)
        if not user_id:
            return redirect(url_for('login'))
        return f(user_id, *args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Redirect to login or status based on session"""
    token = request.cookies.get('session')
    user_id = get_user_from_session(token)
    if user_id:
        return redirect(url_for('status'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login.html', error='Username and password are required')

        conn = get_db_connection()
        user = conn.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            # Create session and set cookie
            token = create_session(user['id'])
            response = make_response(redirect(url_for('status')))
            response.set_cookie('session', token, httponly=True, samesite='Lax', max_age=app.config['SESSION_EXPIRY_HOURS']*3600)
            return response
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout handler"""
    token = request.cookies.get('session')
    if token:
        delete_session(token)

    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response

@app.route('/status')
@login_required
def status(user_id):
    """Status page showing found, unlocked, and missing videos"""
    conn = get_db_connection()

    # Get all videos with found and unlocked status
    videos = conn.execute('''
        SELECT
            v.id,
            v.title,
            v.hint,
            f.found_at,
            u.unlocked_at
        FROM videos v
        LEFT JOIN found f ON v.id = f.video_id AND f.user_id = ?
        LEFT JOIN unlocks u ON v.id = u.video_id AND u.user_id = ?
        ORDER BY v.id
    ''', (user_id, user_id)).fetchall()

    conn.close()

    # Categorize videos
    found_videos = []
    unlocked_videos = []
    missing_videos = []

    for video in videos:
        video_dict = dict(video)
        if video['unlocked_at']:
            unlocked_videos.append(video_dict)
        elif video['found_at']:
            found_videos.append(video_dict)
        else:
            missing_videos.append(video_dict)

    return render_template('status.html',
                         found_videos=found_videos,
                         unlocked_videos=unlocked_videos,
                         missing_videos=missing_videos)

@app.route('/qrscan')
@login_required
def qrscan(user_id):
    """QR code scanning page"""
    return render_template('qrscan.html')

@app.route('/video')
@login_required
def video(user_id):
    """Video page - display video and unlock form"""
    video_id = request.args.get('id', type=int)

    if not video_id:
        return "Video ID required", 400

    conn = get_db_connection()

    # Get video details
    video_data = conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()

    if not video_data:
        conn.close()
        return "Video not found", 404

    # Mark as found if not already
    try:
        conn.execute('INSERT INTO found (user_id, video_id) VALUES (?, ?)', (user_id, video_id))
        conn.commit()
    except sqlite3.IntegrityError:
        # Already found, that's okay
        pass

    # Check if unlocked
    unlocked = conn.execute('SELECT unlocked_at FROM unlocks WHERE user_id = ? AND video_id = ?',
                           (user_id, video_id)).fetchone()

    conn.close()

    return render_template('video.html',
                         video=dict(video_data),
                         is_unlocked=bool(unlocked))

@app.route('/unlock', methods=['POST'])
@login_required
def unlock(user_id):
    """Handle unlock keyword submission"""
    video_id = request.form.get('video_id', type=int)
    keyword = request.form.get('keyword', '').strip()

    if not video_id or not keyword:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    conn = get_db_connection()

    # Get video keyword
    video_data = conn.execute('SELECT keyword FROM videos WHERE id = ?', (video_id,)).fetchone()

    if not video_data:
        conn.close()
        return jsonify({'success': False, 'error': 'Video not found'}), 404

    # Check keyword (case-insensitive)
    if keyword.lower() == video_data['keyword'].lower():
        # Mark as unlocked
        try:
            conn.execute('INSERT INTO unlocks (user_id, video_id) VALUES (?, ?)', (user_id, video_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Video unlocked successfully!'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': True, 'message': 'Video already unlocked!'})
    else:
        conn.close()
        return jsonify({'success': False, 'error': 'Incorrect keyword'})

@app.route('/videos/<path:filename>')
@login_required
def serve_video(user_id, filename):
    """Serve video files"""
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

# Initialize database on startup
if __name__ == '__main__':
    # Create database if it doesn't exist
    if not os.path.exists(app.config['DATABASE']):
        print("Database not found, initializing...")
        init_db()

    # Ensure videos directory exists
    os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)

    # Run the app
    app.run(host='0.0.0.0', port=8080, debug=False)
