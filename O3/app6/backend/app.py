from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
from models import db, Note
import os

def create_app():
    app = Flask(__name__,
                static_folder='../frontend/dist',
                static_url_path='/')
    app.config.from_object('config.Config')
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    @app.before_first_request
    def create_tables():
        db.create_all()

    # Get active (non-archived) notes
    @app.route('/api/notes', methods=['GET'])
    def get_notes():
        notes = Note.query.filter_by(archived=False).all()
        return jsonify([note.to_dict() for note in notes])
    
    # Get archived notes separately
    @app.route('/api/notes/archived', methods=['GET'])
    def get_archived_notes():
        notes = Note.query.filter_by(archived=True).all()
        return jsonify([note.to_dict() for note in notes])

    # Create a new note
    @app.route('/api/notes', methods=['POST'])
    def create_note():
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data:
            abort(400, description="Missing required fields: title and content")
        note = Note(title=data['title'], content=data['content'])
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    
    # Update an existing note (or toggle 'archived' state)
    @app.route('/api/notes/<int:note_id>', methods=['PUT'])
    def update_note(note_id):
        note = Note.query.get_or_404(note_id)
        data = request.get_json()
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        note.archived = data.get('archived', note.archived)
        db.session.commit()
        return jsonify(note.to_dict())
    
    # Delete a note
    @app.route('/api/notes/<int:note_id>', methods=['DELETE'])
    def delete_note(note_id):
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return jsonify({"message": "Note deleted"}), 200

    # Serve static files from the React build (for production)
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    # For production, consider using a WSGI server (e.g., gunicorn)
    app.run(port=6151, debug=True)
