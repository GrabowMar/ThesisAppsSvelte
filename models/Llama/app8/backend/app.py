# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy

# 2. App Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

# 3. Database Models (if needed)
db = SQLAlchemy(app)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    comments = db.relationship('Comment', backref='thread', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)

# 4. Authentication Logic (if needed)
# For simplicity, we will not implement authentication in this example

# 5. Utility Functions
def create_thread(data):
    thread = Thread(title=data['title'], content=data['content'], category=data['category'])
    db.session.add(thread)
    db.session.commit()
    return thread

def get_threads():
    return Thread.query.all()

def create_comment(data):
    comment = Comment(content=data['content'], thread_id=data['thread_id'])
    db.session.add(comment)
    db.session.commit()
    return comment

# 6. API Routes
@app.route('/api/threads', methods=['GET'])
def get_all_threads():
    threads = get_threads()
    return jsonify([{'id': t.id, 'title': t.title, 'content': t.content, 'category': t.category} for t in threads])

@app.route('/api/threads', methods=['POST'])
def create_new_thread():
    data = request.get_json()
    thread = create_thread(data)
    return jsonify({'id': thread.id, 'title': thread.title, 'content': thread.content, 'category': thread.category})

@app.route('/api/threads/<int:thread_id>/comments', methods=['POST'])
def create_new_comment(thread_id):
    data = request.get_json()
    data['thread_id'] = thread_id
    comment = create_comment(data)
    return jsonify({'id': comment.id, 'content': comment.content})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5015')))
