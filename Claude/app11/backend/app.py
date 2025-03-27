# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime, timedelta
import sqlite3
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)

# 3. Database Setup
def get_db_connection():
    conn = sqlite3.connect('polls.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS polls (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        created_by TEXT NOT NULL,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users (id)
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS options (
        id TEXT PRIMARY KEY,
        poll_id TEXT NOT NULL,
        text TEXT NOT NULL,
        FOREIGN KEY (poll_id) REFERENCES polls (id)
    )
    ''')
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS votes (
        id TEXT PRIMARY KEY,
        poll_id TEXT NOT NULL,
        option_id TEXT NOT NULL,
        user_id TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (poll_id) REFERENCES polls (id),
        FOREIGN KEY (option_id) REFERENCES options (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# 4. Authentication & User Management
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'password', 'email')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    try:
        hashed_password = generate_password_hash(data['password'], method='scrypt')
        user_id = str(uuid.uuid4())
        
        conn.execute(
            'INSERT INTO users (id, username, password, email) VALUES (?, ?, ?, ?)',
            (user_id, data['username'], hashed_password, data['email'])
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 409
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'error': 'Missing username or password'}), 400
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (data['username'],)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], data['password']):
        session['user_id'] = user['id']
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
    
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@app.route('/api/user', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'authenticated': False}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
        
    return jsonify({'authenticated': False}), 401

# 5. Poll Management
@app.route('/api/polls', methods=['POST'])
def create_poll():
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    
    if not all(k in data for k in ('title', 'options')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if len(data['options']) < 2:
        return jsonify({'error': 'At least two options are required'}), 400
    
    poll_id = str(uuid.uuid4())
    expires_at = None
    
    if 'expiresIn' in data and data['expiresIn']:
        expires_at = (datetime.now() + timedelta(hours=int(data['expiresIn']))).isoformat()
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO polls (id, title, description, created_by, expires_at) VALUES (?, ?, ?, ?, ?)',
            (poll_id, data['title'], data.get('description', ''), user_id, expires_at)
        )
        
        for option_text in data['options']:
            option_id = str(uuid.uuid4())
            conn.execute(
                'INSERT INTO options (id, poll_id, text) VALUES (?, ?, ?)',
                (option_id, poll_id, option_text)
            )
        
        conn.commit()
        return jsonify({'success': True, 'poll_id': poll_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/polls', methods=['GET'])
def get_polls():
    conn = get_db_connection()
    
    current_time = datetime.now().isoformat()
    
    # Fetch active polls (not expired)
    polls = conn.execute(
        '''
        SELECT p.*, u.username as creator_name 
        FROM polls p
        JOIN users u ON p.created_by = u.id
        WHERE p.expires_at IS NULL OR p.expires_at > ?
        ORDER BY p.created_at DESC
        ''',
        (current_time,)
    ).fetchall()
    
    result = []
    for poll in polls:
        options = conn.execute('SELECT id, text FROM options WHERE poll_id = ?', (poll['id'],)).fetchall()
        
        # Get vote counts for each option
        options_with_votes = []
        total_votes = 0
        for option in options:
            vote_count = conn.execute(
                'SELECT COUNT(*) as count FROM votes WHERE option_id = ?', 
                (option['id'],)
            ).fetchone()['count']
            
            total_votes += vote_count
            options_with_votes.append({
                'id': option['id'],
                'text': option['text'],
                'votes': vote_count
            })
        
        result.append({
            'id': poll['id'],
            'title': poll['title'],
            'description': poll['description'],
            'createdBy': {
                'id': poll['created_by'],
                'username': poll['creator_name']
            },
            'expiresAt': poll['expires_at'],
            'createdAt': poll['created_at'],
            'options': options_with_votes,
            'totalVotes': total_votes
        })
    
    conn.close()
    return jsonify({'polls': result}), 200

@app.route('/api/polls/<poll_id>', methods=['GET'])
def get_poll(poll_id):
    conn = get_db_connection()
    
    poll = conn.execute(
        '''
        SELECT p.*, u.username as creator_name 
        FROM polls p
        JOIN users u ON p.created_by = u.id
        WHERE p.id = ?
        ''',
        (poll_id,)
    ).fetchone()
    
    if not poll:
        conn.close()
        return jsonify({'error': 'Poll not found'}), 404
    
    options = conn.execute('SELECT id, text FROM options WHERE poll_id = ?', (poll_id,)).fetchall()
    
    options_with_votes = []
    total_votes = 0
    for option in options:
        vote_count = conn.execute(
            'SELECT COUNT(*) as count FROM votes WHERE option_id = ?', 
            (option['id'],)
        ).fetchone()['count']
        
        total_votes += vote_count
        options_with_votes.append({
            'id': option['id'],
            'text': option['text'],
            'votes': vote_count
        })
    
    # Check if user has already voted
    user_id = session.get('user_id')
    has_voted = False
    user_vote = None
    
    if user_id:
        vote = conn.execute(
            'SELECT option_id FROM votes WHERE poll_id = ? AND user_id = ?',
            (poll_id, user_id)
        ).fetchone()
        
        if vote:
            has_voted = True
            user_vote = vote['option_id']
    
    result = {
        'id': poll['id'],
        'title': poll['title'],
        'description': poll['description'],
        'createdBy': {
            'id': poll['created_by'],
            'username': poll['creator_name']
        },
        'expiresAt': poll['expires_at'],
        'createdAt': poll['created_at'],
        'options': options_with_votes,
        'totalVotes': total_votes,
        'hasVoted': has_voted,
        'userVote': user_vote
    }
    
    conn.close()
    return jsonify({'poll': result}), 200

@app.route('/api/polls/<poll_id>/vote', methods=['POST'])
def vote(poll_id):
    data = request.get_json()
    
    if 'option_id' not in data:
        return jsonify({'error': 'Option ID is required'}), 400
    
    conn = get_db_connection()
    
    # Verify poll exists and is not expired
    poll = conn.execute(
        'SELECT * FROM polls WHERE id = ? AND (expires_at IS NULL OR expires_at > ?)',
        (poll_id, datetime.now().isoformat())
    ).fetchone()
    
    if not poll:
        conn.close()
        return jsonify({'error': 'Poll not found or expired'}), 404
    
    # Verify option belongs to this poll
    option = conn.execute(
        'SELECT * FROM options WHERE id = ? AND poll_id = ?',
        (data['option_id'], poll_id)
    ).fetchone()
    
    if not option:
        conn.close()
        return jsonify({'error': 'Invalid option'}), 400
    
    # Check if user is logged in
    user_id = session.get('user_id')
    ip_address = request.remote_addr
    
    # Check if user has already voted
    if user_id:
        existing_vote = conn.execute(
            'SELECT * FROM votes WHERE poll_id = ? AND user_id = ?',
            (poll_id, user_id)
        ).fetchone()
        
        if existing_vote:
            conn.close()
            return jsonify({'error': 'You have already voted in this poll'}), 400
    else:
        # For anonymous users, check by IP address
        existing_vote = conn.execute(
            'SELECT * FROM votes WHERE poll_id = ? AND ip_address = ? AND user_id IS NULL',
            (poll_id, ip_address)
        ).fetchone()
        
        if existing_vote:
            conn.close()
            return jsonify({'error': 'You have already voted in this poll from this device'}), 400
    
    # Record the vote
    vote_id = str(uuid.uuid4())
    conn.execute(
        'INSERT INTO votes (id, poll_id, option_id, user_id, ip_address) VALUES (?, ?, ?, ?, ?)',
        (vote_id, poll_id, data['option_id'], user_id, ip_address)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Vote recorded successfully'}), 200

@app.route('/api/my-polls', methods=['GET'])
def get_my_polls():
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    conn = get_db_connection()
    polls = conn.execute(
        'SELECT * FROM polls WHERE created_by = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()
    
    result = []
    for poll in polls:
        options = conn.execute('SELECT id, text FROM options WHERE poll_id = ?', (poll['id'],)).fetchall()
        
        # Get vote counts for each option
        options_with_votes = []
        total_votes = 0
        for option in options:
            vote_count = conn.execute(
                'SELECT COUNT(*) as count FROM votes WHERE option_id = ?', 
                (option['id'],)
            ).fetchone()['count']
            
            total_votes += vote_count
            options_with_votes.append({
                'id': option['id'],
                'text': option['text'],
                'votes': vote_count
            })
        
        # Check if poll is expired
        is_expired = False
        if poll['expires_at']:
            expires_at = datetime.fromisoformat(poll['expires_at'])
            is_expired = datetime.now() > expires_at
        
        result.append({
            'id': poll['id'],
            'title': poll['title'],
            'description': poll['description'],
            'expiresAt': poll['expires_at'],
            'createdAt': poll['created_at'],
            'options': options_with_votes,
            'totalVotes': total_votes,
            'isExpired': is_expired
        })
    
    conn.close()
    return jsonify({'polls': result}), 200

# 6. Analytics
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    conn = get_db_connection()
    
    # Total polls
    total_polls = conn.execute('SELECT COUNT(*) as count FROM polls').fetchone()['count']
    
    # Total votes
    total_votes = conn.execute('SELECT COUNT(*) as count FROM votes').fetchone()['count']
    
    # Active polls (not expired)
    current_time = datetime.now().isoformat()
    active_polls = conn.execute(
        'SELECT COUNT(*) as count FROM polls WHERE expires_at IS NULL OR expires_at > ?',
        (current_time,)
    ).fetchone()['count']
    
    # Most popular polls
    popular_polls = conn.execute(
        '''
        SELECT p.id, p.title, COUNT(v.id) as vote_count
        FROM polls p
        JOIN votes v ON p.id = v.poll_id
        GROUP BY p.id
        ORDER BY vote_count DESC
        LIMIT 5
        '''
    ).fetchall()
    
    popular_polls_result = [
        {
            'id': poll['id'],
            'title': poll['title'],
            'voteCount': poll['vote_count']
        }
        for poll in popular_polls
    ]
    
    # Recent activity
    recent_votes = conn.execute(
        '''
        SELECT v.created_at, p.title, o.text as option_text
        FROM votes v
        JOIN options o ON v.option_id = o.id
        JOIN polls p ON v.poll_id = p.id
        ORDER BY v.created_at DESC
        LIMIT 10
        '''
    ).fetchall()
    
    recent_activity = [
        {
            'timestamp': vote['created_at'],
            'pollTitle': vote['title'],
            'optionText': vote['option_text']
        }
        for vote in recent_votes
    ]
    
    conn.close()
    
    return jsonify({
        'totalPolls': total_polls,
        'totalVotes': total_votes,
        'activePolls': active_polls,
        'popularPolls': popular_polls_result,
        'recentActivity': recent_activity
    }), 200

# 8. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5341')), debug=True)
