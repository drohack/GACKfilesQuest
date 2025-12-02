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

def admin_required(f):
    """Decorator to require admin access for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('session')
        user_id = get_user_from_session(token)
        if not user_id:
            return redirect(url_for('login'))

        # Check if user is admin
        conn = get_db_connection()
        user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        if not user or not user['is_admin']:
            return "Access denied - Admin only", 403

        return f(user_id, *args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Redirect to login, intro, or status based on session"""
    token = request.cookies.get('session')
    user_id = get_user_from_session(token)
    if user_id:
        # Check if user has seen intro
        conn = get_db_connection()
        user = conn.execute('SELECT seen_intro FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        if user and not user['seen_intro']:
            return redirect(url_for('intro'))
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and handler"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # Validation
        if not username or not password:
            return render_template('register.html', error='Username and password are required')

        if len(username) < 3:
            return render_template('register.html', error='Username must be at least 3 characters')

        if len(password) < 4:
            return render_template('register.html', error='Password must be at least 4 characters')

        if password != password_confirm:
            return render_template('register.html', error='Passwords do not match')

        # Create user
        conn = get_db_connection()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            conn.execute('INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                        (username, password_hash, 0))
            conn.commit()
            conn.close()

            # Auto-login after registration and redirect to intro
            conn = get_db_connection()
            user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()

            token = create_session(user['id'])
            response = make_response(redirect(url_for('intro')))
            response.set_cookie('session', token, httponly=True, samesite='Lax', max_age=app.config['SESSION_EXPIRY_HOURS']*3600)
            return response

        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Username already exists')

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout handler"""
    token = request.cookies.get('session')
    if token:
        delete_session(token)

    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response

@app.route('/intro')
@login_required
def intro(user_id):
    """Intro/briefing page with mission video"""
    return render_template('intro.html')

@app.route('/mark-intro-seen', methods=['POST'])
@login_required
def mark_intro_seen(user_id):
    """Mark that user has seen the intro"""
    conn = get_db_connection()
    conn.execute('UPDATE users SET seen_intro = 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/status')
@login_required
def status(user_id):
    """Status page showing found, unlocked, and missing videos"""
    conn = get_db_connection()

    # Check if user is admin
    user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
    is_admin = user['is_admin'] if user else 0

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

    # Convert to list of dicts and calculate counts
    videos_list = [dict(video) for video in videos]
    total_count = len(videos_list)
    found_count = sum(1 for v in videos_list if v['found_at'])
    unlocked_count = sum(1 for v in videos_list if v['unlocked_at'])

    # Check if all videos are unlocked (cryptid identified)
    all_solved = (unlocked_count == total_count and total_count > 0)

    return render_template('status.html',
                         videos=videos_list,
                         total_count=total_count,
                         found_count=found_count,
                         unlocked_count=unlocked_count,
                         is_admin=is_admin,
                         all_solved=all_solved)

@app.route('/qr/<scan_code>')
def qr_redirect(scan_code):
    """Handle QR code URL access - redirects to login/main page"""
    # If someone scans with third-party scanner and clicks the URL,
    # just redirect them to the appropriate page
    token = request.cookies.get('session')
    user_id = get_user_from_session(token)

    if user_id:
        # Logged in - redirect to field reports
        return redirect(url_for('status'))
    else:
        # Not logged in - redirect to login
        return redirect(url_for('login'))

@app.route('/qrscan')
@login_required
def qrscan(user_id):
    """QR code scanning page"""
    return render_template('qrscan.html')

@app.route('/verify-scan', methods=['POST'])
@login_required
def verify_scan(user_id):
    """Verify scanned code and mark video as found"""
    scan_code = request.json.get('code', '').strip()

    if not scan_code:
        return jsonify({'success': False, 'error': 'No scan code provided'}), 400

    conn = get_db_connection()

    # Look up video by scan code
    video = conn.execute('SELECT id FROM videos WHERE scan_code = ?', (scan_code,)).fetchone()

    if not video:
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid scan code'}), 404

    video_id = video['id']

    # Mark as found
    try:
        conn.execute('INSERT INTO found (user_id, video_id) VALUES (?, ?)', (user_id, video_id))
        conn.commit()
    except sqlite3.IntegrityError:
        # Already found, that's okay
        pass

    conn.close()

    return jsonify({'success': True, 'video_id': video_id})

@app.route('/video')
@login_required
def video(user_id):
    """Video page - display video and unlock form"""
    video_id = request.args.get('id', type=int)

    if not video_id:
        # No ID provided - show no access
        return render_template('no_access.html', video_title='UNKNOWN')

    conn = get_db_connection()

    # Get video details
    video_data = conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()

    if not video_data:
        conn.close()
        # Invalid video ID - show no access
        return render_template('no_access.html', video_title='INVALID ID')

    # Check if user has found this video (scanned the QR code)
    found = conn.execute('SELECT found_at FROM found WHERE user_id = ? AND video_id = ?',
                        (user_id, video_id)).fetchone()

    if not found:
        conn.close()
        # User hasn't scanned the QR code - show no access
        return render_template('no_access.html', video_title=video_data['title'])

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

@app.route('/admin')
@admin_required
def admin(user_id):
    """Admin panel for managing videos and users"""
    conn = get_db_connection()

    # Get all videos
    videos = conn.execute('SELECT * FROM videos ORDER BY id').fetchall()

    # Get all users
    users = conn.execute('SELECT id, username, is_admin FROM users ORDER BY id').fetchall()

    conn.close()

    return render_template('admin.html',
                         videos=[dict(v) for v in videos],
                         users=[dict(u) for u in users])

@app.route('/admin/edit-video', methods=['POST'])
@admin_required
def admin_edit_video(user_id):
    """Handle video edit from admin panel"""
    video_id = request.form.get('video_id', type=int)
    title = request.form.get('title', '').strip()
    scan_code = request.form.get('scan_code', '').strip()
    keyword = request.form.get('keyword', '').strip()
    hint = request.form.get('hint', '').strip()
    filename = request.form.get('filename', '').strip()

    if not video_id:
        return jsonify({'success': False, 'error': 'Video ID required'}), 400

    conn = get_db_connection()

    # Build update query dynamically based on provided fields
    updates = []
    params = []

    if title:
        updates.append('title = ?')
        params.append(title)
    if scan_code:
        updates.append('scan_code = ?')
        params.append(scan_code)
    if keyword:
        updates.append('keyword = ?')
        params.append(keyword)
    if hint:
        updates.append('hint = ?')
        params.append(hint)
    if filename:
        updates.append('filename = ?')
        params.append(filename)

    if not updates:
        return jsonify({'success': False, 'error': 'No fields to update'}), 400

    params.append(video_id)
    query = f"UPDATE videos SET {', '.join(updates)} WHERE id = ?"

    try:
        conn.execute(query, params)
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Video updated successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Scan code must be unique'}), 400

@app.route('/admin/reset-password', methods=['POST'])
@admin_required
def admin_reset_password(user_id):
    """Handle password reset from admin panel"""
    username = request.form.get('username', '').strip()
    new_password = request.form.get('new_password', '').strip()

    if not username or not new_password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400

    conn = get_db_connection()

    # Check if user exists
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'error': 'User not found'}), 404

    # Hash and update password
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    conn.execute('UPDATE users SET password_hash = ? WHERE username = ?',
                (password_hash, username))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'Password reset for {username}'})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors - redirect to main page"""
    # Check if user is logged in
    token = request.cookies.get('session')
    user_id = get_user_from_session(token)

    if user_id:
        # Logged in - redirect to field reports
        return redirect(url_for('status'))
    else:
        # Not logged in - redirect to login
        return redirect(url_for('login'))

# Initialize database on startup
if __name__ == '__main__':
    # Create database if it doesn't exist
    if not os.path.exists(app.config['DATABASE']):
        print("Database not found, initializing...")
        init_db()

    # Ensure videos directory exists
    os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)

    # Run the app (HTTP only - SSL handled by reverse proxy)
    print("Starting server on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
