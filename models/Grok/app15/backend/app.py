# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
import jwt
import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kanban.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    column_id = db.Column(db.Integer, db.ForeignKey('column.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)

# 4. Authentication Logic
def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        token = generate_token(user.id)
        return jsonify({'token': token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401

# 5. Utility Functions
def get_current_user():
    token = request.headers.get('Authorization')
    if token:
        user_id = verify_token(token.split()[1])
        if user_id:
            return User.query.get(user_id)
    return None

# 6. API Routes
@app.route('/boards', methods=['GET', 'POST'])
def manage_boards():
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401

    if request.method == 'GET':
        boards = Board.query.filter_by(user_id=user.id).all()
        return jsonify([{'id': board.id, 'name': board.name} for board in boards]), 200

    if request.method == 'POST':
        data = request.get_json()
        new_board = Board(name=data.get('name'), user_id=user.id)
        db.session.add(new_board)
        db.session.commit()
        return jsonify({'id': new_board.id, 'name': new_board.name}), 201

@app.route('/boards/<int:board_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_board(board_id):
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401

    board = Board.query.get(board_id)
    if not board or board.user_id != user.id:
        return jsonify({'message': 'Board not found'}), 404

    if request.method == 'GET':
        columns = Column.query.filter_by(board_id=board_id).order_by(Column.position).all()
        return jsonify({
            'id': board.id,
            'name': board.name,
            'columns': [{'id': col.id, 'name': col.name, 'position': col.position} for col in columns]
        }), 200

    if request.method == 'PUT':
        data = request.get_json()
        board.name = data.get('name', board.name)
        db.session.commit()
        return jsonify({'id': board.id, 'name': board.name}), 200

    if request.method == 'DELETE':
        db.session.delete(board)
        db.session.commit()
        return jsonify({'message': 'Board deleted successfully'}), 200

@app.route('/boards/<int:board_id>/columns', methods=['POST'])
def add_column(board_id):
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401

    board = Board.query.get(board_id)
    if not board or board.user_id != user.id:
        return jsonify({'message': 'Board not found'}), 404

    data = request.get_json()
    max_position = db.session.query(db.func.max(Column.position)).filter_by(board_id=board_id).scalar() or 0
    new_column = Column(name=data.get('name'), board_id=board_id, position=max_position + 1)
    db.session.add(new_column)
    db.session.commit()

    return jsonify({'id': new_column.id, 'name': new_column.name, 'position': new_column.position}), 201

@app.route('/columns/<int:column_id>', methods=['PUT', 'DELETE'])
def manage_column(column_id):
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401

    column = Column.query.get(column_id)
    if not column:
        return jsonify({'message': 'Column not found'}), 404

    board = Board.query.get(column.board_id)
    if not board or board.user_id != user.id:
        return jsonify({'message': 'Unauthorized'}), 401

    if request.method == 'PUT':
        data = request.get_json()
        column.name = data.get('name', column.name)
        new_position = data.get('position')
        if new_position is not None:
            columns = Column.query.filter_by(board_id=column.board_id).order_by(Column.position).all()
            if new_position < column.position:
                for col in columns:
                    if col.position >= new_position and col.position < column.position:
                        col.position += 1
            elif new_position > column.position:
                for col in columns:
                    if col.position > column.position and col.position <= new_position:
                        col.position -= 1
            column.position = new_position
        db.session.commit()
        return jsonify({'id': column.id, 'name': column.name, 'position': column.position}), 200

    if request.method == 'DELETE':
        tasks = Task.query.filter_by(column_id=column.id).all()
        for task in tasks:
            db.session.delete(task)
        db.session.delete(column)
        db.session.commit()
        return jsonify({'message': 'Column deleted successfully'}), 200

@app.route('/columns/<int:column_id>/tasks', methods=['POST'])
def add_task(column_id):
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401

    column = Column.query.get(column_id)
    if not column:
        return jsonify({'message': 'Column not found'}), 404

    board = Board.query.get(column.board_id)
    if not board or board.user_id != user.id:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    max_position = db.session.query(db.func.max(Task.position)).filter_by(column_id=column_id).scalar() or 0
    new_task = Task(title=data.get('title'), description=data.get('description'), column_id=column_id, position=max_position + 1)
    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        'id': new_task.id,
        'title': new_task.title,
        'description': new_task.description,
        'column_id': new_task.column_id,
        'position': new_task.position
    }), 201

@app.route('/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_task(task_id):
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401

    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    column = Column.query.get(task.column_id)
    board = Board.query.get(column.board_id)
    if not board or board.user_id != user.id:
        return jsonify({'message': 'Unauthorized'}), 401

    if request.method == 'GET':
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'column_id': task.column_id,
            'position': task.position
        }), 200

    if request.method == 'PUT':
        data = request.get_json()
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        new_position = data.get('position')
        new_column_id = data.get('column_id')
        if new_position is not None or new_column_id is not None:
            if new_column_id is not None and new_column_id != task.column_id:
                old_column = Column.query.get(task.column_id)
                new_column = Column.query.get(new_column_id)
                if not new_column or new_column.board_id != old_column.board_id:
                    return jsonify({'message': 'Invalid column'}), 400
                task.column_id = new_column_id
                new_position = new_position if new_position is not None else 0
            else:
                new_column_id = task.column_id
                new_position = new_position if new_position is not None else task.position

            tasks = Task.query.filter_by(column_id=new_column_id).order_by(Task.position).all()
            if new_position < task.position:
                for t in tasks:
                    if t.position >= new_position and t.position < task.position and t.id != task.id:
                        t.position += 1
            elif new_position > task.position:
                for t in tasks:
                    if t.position > task.position and t.position <= new_position and t.id != task.id:
                        t.position -= 1
            task.position = new_position

        db.session.commit()
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'column_id': task.column_id,
            'position': task.position
        }), 200

    if request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5509')))
