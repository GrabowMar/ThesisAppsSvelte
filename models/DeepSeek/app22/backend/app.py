from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json

# App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'dev-secret-key'  # Change this in production
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

# Database Initialization
def init_db():
    conn = sqlite3.connect('language_learning.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            current_language TEXT DEFAULT 'English',
            level INTEGER DEFAULT 1
        )
    ''')
    
    # User progress table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id TEXT,
            language TEXT,
            vocabulary_learned INTEGER DEFAULT 0,
            grammar_learned INTEGER DEFAULT 0,
            quizzes_completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            PRIMARY KEY (user_id, language)
        )
    ''')
    
    # Vocabulary lessons
    c.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            word TEXT,
            translation TEXT,
            category TEXT,
            example TEXT
        )
    ''')
    
    # Grammar exercises
    c.execute('''
        CREATE TABLE IF NOT EXISTS grammar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            topic TEXT,
            explanation TEXT,
            example TEXT
        )
    ''')
    
    # Quizzes
    c.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            question TEXT,
            options TEXT,  # JSON array
            correct_answer TEXT
        )
    ''')
    
    # Pronunciation guides
    c.execute('''
        CREATE TABLE IF NOT EXISTS pronunciation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            sound TEXT,
            description TEXT,
            audio_file TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('language_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database with sample data
def seed_database():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if data already exists
    c.execute("SELECT COUNT(*) FROM vocabulary")
    if c.fetchone()[0] == 0:
        # Sample vocabulary
        vocab_data = [
            ('Spanish', 'hola', 'hello', 'greetings', 'Hola, ¿cómo estás?'),
            ('French', 'bonjour', 'hello', 'greetings', 'Bonjour, comment ça va?'),
            ('German', 'hallo', 'hello', 'greetings', 'Hallo, wie geht es dir?')
        ]
        c.executemany("INSERT INTO vocabulary (language, word, translation, category, example) VALUES (?, ?, ?, ?, ?)", vocab_data)
        
        # Sample grammar
        grammar_data = [
            ('Spanish', 'Present Tense', 'The present tense is used to describe current actions...', 'Yo hablo español'),
            ('French', 'Gender of Nouns', 'Nouns in French are either masculine or feminine...', 'La maison (feminine)'),
            ('German', 'Word Order', 'The basic word order in German is subject-verb-object...', 'Ich esse einen Apfel')
        ]
        c.executemany("INSERT INTO grammar (language, topic, explanation, example) VALUES (?, ?, ?, ?)", grammar_data)
        
        # Sample quizzes
        quiz_data = [
            ('Spanish', 'What does "hola" mean?', '["Goodbye", "Hello", "Thank you", "Please"]', 'Hello'),
            ('French', 'How do you say "thank you" in French?', '["Bonjour", "Merci", "Au revoir", "S\'il vous plaît"]', 'Merci'),
            ('German', 'What is the correct article for "Haus"?', '["der", "die", "das", "den"]', 'das')
        ]
        c.executemany("INSERT INTO quizzes (language, question, options, correct_answer) VALUES (?, ?, ?, ?)", quiz_data)
        
        # Sample pronunciation
        pronunciation_data = [
            ('Spanish', 'll', 'Pronounced like "y" in "yes" in most dialects', 'llamar.mp3'),
            ('French', 'r', 'Guttural sound made in the back of the throat', 'rouge.mp3'),
            ('German', 'ch', 'Two sounds: after a, o, u like in "Bach"; otherwise, softer', 'ich.mp3')
        ]
        c.executemany("INSERT INTO pronunciation (language, sound, description, audio_file) VALUES (?, ?, ?, ?)", pronunciation_data)
        
        conn.commit()
    
    conn.close()

# Initialize and seed database on startup
init_db()
seed_database()

# Utility Functions
def get_user_id():
    if 'user_id' not in session:
        return None
    return session['user_id']

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    try:
        conn = get_db_connection()
        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        
        conn.execute(
            "INSERT INTO users (id, username, password, email) VALUES (?, ?, ?, ?)",
            (user_id, username, hashed_password, email)
        )
        conn.commit()
        
        # Initialize progress for default language
        conn.execute(
            "INSERT INTO user_progress (user_id, language) VALUES (?, ?)",
            (user_id, 'English')
        )
        conn.commit()
        
        session['user_id'] = user_id
        return jsonify({'message': 'User created successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username or email already exists'}), 400
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user is None or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    session['user_id'] = user['id']
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    user_id = get_user_id()
    if user_id is None:
        return jsonify({'authenticated': False}), 200
    
    conn = get_db_connection()
    user = conn.execute('SELECT id, username, current_language, level FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user is None:
        return jsonify({'authenticated': False}), 200
    
    return jsonify({
        'authenticated': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'current_language': user['current_language'],
            'level': user['level']
        }
    }), 200

# Learning Content Routes
@app.route('/api/languages', methods=['GET'])
def get_available_languages():
    conn = get_db_connection()
    languages = conn.execute('SELECT DISTINCT language FROM vocabulary').fetchall()
    conn.close()
    return jsonify([lang['language'] for lang in languages]), 200

@app.route('/api/vocabulary/<language>', methods=['GET'])
def get_vocabulary_lessons(language):
    level = request.args.get('level', default=1, type=int)
    category = request.args.get('category', default=None)
    
    query = 'SELECT * FROM vocabulary WHERE language = ?'
    params = [language]
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    conn = get_db_connection()
    lessons = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(lesson) for lesson in lessons]), 200

@app.route('/api/grammar/<language>', methods=['GET'])
def get_grammar_exercises(language):
    level = request.args.get('level', default=1, type=int)
    topic = request.args.get('topic', default=None)
    
    query = 'SELECT * FROM grammar WHERE language = ?'
    params = [language]
    
    if topic:
        query += ' AND topic = ?'
        params.append(topic)
    
    conn = get_db_connection()
    exercises = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(exercise) for exercise in exercises]), 200

@app.route('/api/pronunciation/<language>', methods=['GET'])
def get_pronunciation_guides(language):
    conn = get_db_connection()
    guides = conn.execute('SELECT * FROM pronunciation WHERE language = ?', (language,)).fetchall()
    conn.close()
    return jsonify([dict(guide) for guide in guides]), 200

@app.route('/api/quizzes/<language>', methods=['GET'])
def get_quizzes(language):
    level = request.args.get('level', default=1, type=int)
    
    conn = get_db_connection()
    quizzes = conn.execute('SELECT * FROM quizzes WHERE language = ?', (language,)).fetchall()
    conn.close()
    
    # Convert options JSON string to array
    quiz_list = [dict(quiz) for quiz in quizzes]
    for quiz in quiz_list:
        quiz['options'] = json.loads(quiz['options'])
    
    return jsonify(quiz_list), 200

@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    user_id = get_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    quiz_id = data.get('quiz_id')
    selected_answer = data.get('selected_answer')
    
    if not quiz_id or selected_answer is None:
        return jsonify({'error': 'Quiz ID and answer are required'}), 400
    
    conn = get_db_connection()
    
    # Get quiz
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    if quiz is None:
        conn.close()
        return jsonify({'error': 'Quiz not found'}), 404
    
    is_correct = selected_answer == quiz['correct_answer']
    
    if is_correct:
        # Update user progress
        conn.execute('''
            UPDATE user_progress 
            SET quizzes_completed = quizzes_completed + 1 
            WHERE user_id = ? AND language = ?
        ''', (user_id, quiz['language']))
        conn.commit()
    
    conn.close()
    
    return jsonify({
        'is_correct': is_correct,
        'correct_answer': quiz['correct_answer']
    }), 200

# Progress Tracking
@app.route('/api/progress', methods=['GET'])
def get_user_progress():
    user_id = get_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    user = conn.execute('SELECT current_language FROM users WHERE id = ?', (user_id,)).fetchone()
    if user is None:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    progress = conn.execute('''
        SELECT * FROM user_progress 
        WHERE user_id = ? AND language = ?
    ''', (user_id, user['current_language'])).fetchone()
    
    languages = conn.execute('''
        SELECT language, vocabulary_learned, grammar_learned, quizzes_completed 
        FROM user_progress 
        WHERE user_id = ?
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    if progress is None:
        return jsonify({'error': 'Progress not found'}), 404
    
    return jsonify({
        'current_language': user['current_language'],
        'current_progress': dict(progress),
        'all_languages': [dict(lang) for lang in languages]
    }), 200

@app.route('/api/change-language', methods=['POST'])
def change_language():
    user_id = get_user_id()
    if user_id is None:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    language = data.get('language')
    if not language:
        return jsonify({'error': 'Language is required'}), 400
    
    conn = get_db_connection()
    
    # Check if progress exists for this language, create if not
    progress = conn.execute('''
        SELECT 1 FROM user_progress 
        WHERE user_id = ? AND language = ?
    ''', (user_id, language)).fetchone()
    
    if not progress:
        conn.execute('''
            INSERT INTO user_progress (user_id, language)
            VALUES (?, ?)
        ''', (user_id, language))
        conn.commit()
    
    # Update user's current language
    conn.execute('''
        UPDATE users 
        SET current_language = ? 
        WHERE id = ?
    ''', (language, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Language updated successfully'}), 200

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5203')))
