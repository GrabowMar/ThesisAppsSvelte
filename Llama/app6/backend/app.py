# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# Create a SQLite database for storing notes
conn = sqlite3.connect('notes.db')
c = conn.cursor()

# Create table
c.execute("""CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            category TEXT,
            archived INTEGER
            )""")

conn.commit()
conn.close()

# 4. Authentication Logic (if needed)
# No authentication logic is required for this application

# 5. Utility Functions
def get_all_notes():
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notes")
    notes = c.fetchall()
    conn.close()
    return notes

def get_note(id):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE id=?", (id,))
    note = c.fetchone()
    conn.close()
    return note

def create_note(title, content, category):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (title, content, category, archived) VALUES (?, ?, ?, 0)", (title, content, category))
    conn.commit()
    conn.close()

def update_note(id, title, content, category):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("UPDATE notes SET title=?, content=?, category=? WHERE id=?", (title, content, category, id))
    conn.commit()
    conn.close()

def delete_note(id):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id=?", (id,))
    conn.commit()
    conn.close()

def archive_note(id):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("UPDATE notes SET archived=1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

def search_notes(query):
    conn = sqlite3.connect('notes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE title LIKE ? OR content LIKE ?", ('%' + query + '%', '%' + query + '%'))
    notes = c.fetchall()
    conn.close()
    return notes

# 6. API Routes
@app.route('/api/notes', methods=['GET'])
def get_all_notes_api():
    notes = get_all_notes()
    return jsonify(notes)

@app.route('/api/note/<int:id>', methods=['GET'])
def get_note_api(id):
    note = get_note(id)
    return jsonify(note)

@app.route('/api/create-note', methods=['POST'])
def create_note_api():
    data = request.json
    title = data['title']
    content = data['content']
    category = data['category']
    create_note(title, content, category)
    return jsonify({'message': 'Note created successfully'})

@app.route('/api/update-note/<int:id>', methods=['POST'])
def update_note_api(id):
    data = request.json
    title = data['title']
    content = data['content']
    category = data['category']
    update_note(id, title, content, category)
    return jsonify({'message': 'Note updated successfully'})

@app.route('/api/delete-note/<int:id>', methods=['POST'])
def delete_note_api(id):
    delete_note(id)
    return jsonify({'message': 'Note deleted successfully'})

@app.route('/api/archive-note/<int:id>', methods=['POST'])
def archive_note_api(id):
    archive_note(id)
    return jsonify({'message': 'Note archived successfully'})

@app.route('/api/search-notes', methods=['POST'])
def search_notes_api():
    data = request.json
    query = data['query']
    notes = search_notes(query)
    return jsonify(notes)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5011')))
