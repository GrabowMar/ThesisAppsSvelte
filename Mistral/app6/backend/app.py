from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
db = SQLAlchemy(app)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    archived = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Note {self.title}>'

db.create_all()

@app.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    new_note = Note(title=data['title'], content=data['content'], category=data['category'])
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'message': 'Note created successfully'}), 201

@app.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.filter_by(archived=False).all()
    return jsonify([{'id': note.id, 'title': note.title, 'content': note.content, 'category': note.category} for note in notes])

@app.route('/notes/<int:id>', methods=['GET'])
def get_note(id):
    note = Note.query.get_or_404(id)
    return jsonify({'id': note.id, 'title': note.title, 'content': note.content, 'category': note.category})

@app.route('/notes/<int:id>', methods=['PUT'])
def update_note(id):
    data = request.get_json()
    note = Note.query.get_or_404(id)
    note.title = data['title']
    note.content = data['content']
    note.category = data['category']
    db.session.commit()
    return jsonify({'message': 'Note updated successfully'})

@app.route('/notes/<int:id>', methods=['DELETE'])
def archive_note(id):
    note = Note.query.get_or_404(id)
    note.archived = True
    db.session.commit()
    return jsonify({'message': 'Note archived successfully'})

@app.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('query')
    notes = Note.query.filter(Note.title.contains(query) | Note.content.contains(query)).filter_by(archived=False).all()
    return jsonify([{'id': note.id, 'title': note.title, 'content': note.content, 'category': note.category} for note in notes])

if __name__ == '__main__':
    app.run(debug=True, port=5091)  # Backend port number
