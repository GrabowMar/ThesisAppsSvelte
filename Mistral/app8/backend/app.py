from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    threads = db.relationship('Thread', backref='category', lazy=True)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='thread', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.before_first_request
def create_tables():
    db.create_all()

# Routes
@app.route('/categories', methods=['POST'])
def create_category():
    data = request.json
    new_category = Category(name=data['name'])
    db.session.add(new_category)
    db.session.commit()
    return jsonify({'message': 'Category created successfully'}), 201

@app.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{'id': category.id, 'name': category.name} for category in categories]), 200

@app.route('/threads', methods=['POST'])
def create_thread():
    data = request.json
    new_thread = Thread(title=data['title'], content=data['content'], category_id=data['category_id'])
    db.session.add(new_thread)
    db.session.commit()
    return jsonify({'message': 'Thread created successfully'}), 201

@app.route('/threads', methods=['GET'])
def get_threads():
    threads = Thread.query.all()
    return jsonify([{'id': thread.id, 'title': thread.title, 'content': thread.content, 'category_id': thread.category_id, 'created_at': thread.created_at} for thread in threads]), 200

@app.route('/threads/<int:thread_id>/comments', methods=['POST'])
def create_comment(thread_id):
    data = request.json
    new_comment = Comment(content=data['content'], thread_id=thread_id)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({'message': 'Comment created successfully'}), 201

@app.route('/threads/<int:thread_id>/comments', methods=['GET'])
def get_comments(thread_id):
    comments = Comment.query.filter_by(thread_id=thread_id).all()
    return jsonify([{'id': comment.id, 'content': comment.content, 'created_at': comment.created_at} for comment in comments]), 200

@app.route('/threads/search', methods=['GET'])
def search_threads():
    query = request.args.get('query')
    threads = Thread.query.filter(Thread.title.like(f'%{query}%')).all()
    return jsonify([{'id': thread.id, 'title': thread.title, 'content': thread.content, 'category_id': thread.category_id, 'created_at': thread.created_at} for thread in threads]), 200

@app.route('/threads/sort', methods=['GET'])
def sort_threads():
    sort_by = request.args.get('sort_by')
    if sort_by == 'created_at':
        threads = Thread.query.order_by(Thread.created_at.desc()).all()
    else:
        threads = Thread.query.all()
    return jsonify([{'id': thread.id, 'title': thread.title, 'content': thread.content, 'category_id': thread.category_id, 'created_at': thread.created_at} for thread in threads]), 200

if __name__ == '__main__':
    app.run(port=5095)
