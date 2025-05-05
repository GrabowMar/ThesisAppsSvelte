# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database (In-memory for simplicity)
notes = []
next_note_id = 1

# 4. Utility Functions
def find_note(note_id):
    for note in notes:
        if note['id'] == note_id:
            return note
    return None

# 5. API Routes
@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Retrieves all notes."""
    category = request.args.get('category')
    query = request.args.get('query')
    archived = request.args.get('archived')

    filtered_notes = notes

    if category:
        filtered_notes = [note for note in filtered_notes if note.get('category') == category]

    if query:
        filtered_notes = [note for note in filtered_notes if query.lower() in note['title'].lower() or query.lower() in note['content'].lower()]

    if archived is not None: # Check for None explicitly.  Boolean true/false works too.
        try:
            archived_bool = archived.lower() == 'true'
        except:
            return jsonify({'error': 'Invalid archived filter'}), 400

        filtered_notes = [note for note in filtered_notes if note.get('archived', False) == archived_bool]


    return jsonify(filtered_notes)

@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Retrieves a specific note by ID."""
    note = find_note(note_id)
    if note:
        return jsonify(note)
    return jsonify({'error': 'Note not found'}), 404


@app.route('/api/notes', methods=['POST'])
def create_note():
    """Creates a new note."""
    global next_note_id
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'error': 'Title and content are required'}), 400

    new_note = {
        'id': next_note_id,
        'title': data['title'],
        'content': data['content'],
        'category': data.get('category', 'Uncategorized'),  # Optional category
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat(),
        'archived': False
    }
    notes.append(new_note)
    next_note_id += 1
    return jsonify(new_note), 201

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Updates an existing note."""
    note = find_note(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    note['title'] = data.get('title', note['title'])
    note['content'] = data.get('content', note['content'])
    note['category'] = data.get('category', note['category'])
    note['updated_at'] = datetime.datetime.now().isoformat() # Update timestamp
    note['archived'] = data.get('archived', note['archived']) # Allow archiving

    return jsonify(note)


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Deletes a note."""
    global notes
    original_length = len(notes)
    notes = [note for note in notes if note['id'] != note_id]
    if len(notes) < original_length:
        return jsonify({'message': 'Note deleted'}), 200
    return jsonify({'error': 'Note not found'}), 404

# 6. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

# 7. Start app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5411')), debug=True)
