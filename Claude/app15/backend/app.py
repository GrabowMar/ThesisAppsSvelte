# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key-for-development')
jwt = JWTManager(app)

# 3. Database Models (In-memory for simplicity)
# In a production app, you would use a proper database
users = {}
boards = {}
columns = {}
tasks = {}

# 4. Utility Functions
def save_data():
    """Save data to disk for persistence"""
    data = {
        'users': users,
        'boards': boards,
        'columns': columns,
        'tasks': tasks
    }
    try:
        with open('kanban_data.json', 'w') as f:
            json.dump(data, f)
    except Exception as e:
        app.logger.error(f"Error saving data: {e}")

def load_data():
    """Load data from disk if exists"""
    try:
        if os.path.exists('kanban_data.json'):
            with open('kanban_data.json', 'r') as f:
                data = json.load(f)
                global users, boards, columns, tasks
                users = data.get('users', {})
                boards = data.get('boards', {})
                columns = data.get('columns', {})
                tasks = data.get('tasks', {})
    except Exception as e:
        app.logger.error(f"Error loading data: {e}")

# 5. Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password or not name:
        return jsonify({'error': 'Missing required fields'}), 400
        
    if email in users:
        return jsonify({'error': 'User already exists'}), 409
    
    user_id = str(uuid.uuid4())
    users[email] = {
        'id': user_id,
        'email': email,
        'name': name,
        'password_hash': generate_password_hash(password),
        'created_at': datetime.now().isoformat()
    }
    
    save_data()
    
    access_token = create_access_token(identity=email)
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user_id,
            'email': email,
            'name': name
        }
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400
        
    user = users.get(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=email)
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['name']
        }
    })

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user = get_jwt_identity()
    user = users.get(current_user)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'id': user['id'],
        'email': user['email'],
        'name': user['name']
    })

# 6. Board Routes
@app.route('/api/boards', methods=['GET'])
@jwt_required()
def get_boards():
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    user_boards = [board for board in boards.values() if board['owner_id'] == user_id]
    return jsonify(user_boards)

@app.route('/api/boards', methods=['POST'])
@jwt_required()
def create_board():
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Board name is required'}), 400
    
    board_id = str(uuid.uuid4())
    board = {
        'id': board_id,
        'name': name,
        'owner_id': user_id,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    boards[board_id] = board
    
    # Create default columns
    default_columns = ['To Do', 'In Progress', 'Done']
    for i, column_name in enumerate(default_columns):
        column_id = str(uuid.uuid4())
        columns[column_id] = {
            'id': column_id,
            'name': column_name,
            'board_id': board_id,
            'position': i,
            'created_at': datetime.now().isoformat()
        }
    
    save_data()
    
    return jsonify(board), 201

@app.route('/api/boards/<board_id>', methods=['GET'])
@jwt_required()
def get_board(board_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    board = boards.get(board_id)
    if not board:
        return jsonify({'error': 'Board not found'}), 404
        
    if board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    board_columns = [col for col in columns.values() if col['board_id'] == board_id]
    board_columns.sort(key=lambda x: x['position'])
    
    board_tasks = {}
    for column in board_columns:
        column_tasks = [task for task in tasks.values() if task['column_id'] == column['id']]
        column_tasks.sort(key=lambda x: x['position'])
        board_tasks[column['id']] = column_tasks
    
    return jsonify({
        'board': board,
        'columns': board_columns,
        'tasks': board_tasks
    })

@app.route('/api/boards/<board_id>', methods=['PUT'])
@jwt_required()
def update_board(board_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    board = boards.get(board_id)
    if not board:
        return jsonify({'error': 'Board not found'}), 404
        
    if board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    name = data.get('name')
    
    if name:
        board['name'] = name
    
    board['updated_at'] = datetime.now().isoformat()
    save_data()
    
    return jsonify(board)

@app.route('/api/boards/<board_id>', methods=['DELETE'])
@jwt_required()
def delete_board(board_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    board = boards.get(board_id)
    if not board:
        return jsonify({'error': 'Board not found'}), 404
        
    if board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Delete all related columns
    board_columns = [col for col in columns.values() if col['board_id'] == board_id]
    for col in board_columns:
        # Delete all tasks in this column
        column_tasks = [task for task in tasks.values() if task['column_id'] == col['id']]
        for task in column_tasks:
            del tasks[task['id']]
        del columns[col['id']]
    
    del boards[board_id]
    save_data()
    
    return jsonify({'message': 'Board deleted successfully'})

# 7. Column Routes
@app.route('/api/boards/<board_id>/columns', methods=['POST'])
@jwt_required()
def create_column(board_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    board = boards.get(board_id)
    if not board:
        return jsonify({'error': 'Board not found'}), 404
        
    if board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Column name is required'}), 400
    
    # Get the highest position
    board_columns = [col for col in columns.values() if col['board_id'] == board_id]
    position = max([col.get('position', 0) for col in board_columns], default=-1) + 1
    
    column_id = str(uuid.uuid4())
    column = {
        'id': column_id,
        'name': name,
        'board_id': board_id,
        'position': position,
        'created_at': datetime.now().isoformat()
    }
    
    columns[column_id] = column
    save_data()
    
    return jsonify(column), 201

@app.route('/api/columns/<column_id>', methods=['PUT'])
@jwt_required()
def update_column(column_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    column = columns.get(column_id)
    if not column:
        return jsonify({'error': 'Column not found'}), 404
    
    board = boards.get(column['board_id'])
    if not board or board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    name = data.get('name')
    position = data.get('position')
    
    if name:
        column['name'] = name
    
    if position is not None:
        column['position'] = position
    
    save_data()
    
    return jsonify(column)

@app.route('/api/columns/<column_id>', methods=['DELETE'])
@jwt_required()
def delete_column(column_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    column = columns.get(column_id)
    if not column:
        return jsonify({'error': 'Column not found'}), 404
    
    board = boards.get(column['board_id'])
    if not board or board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Delete all tasks in this column
    column_tasks = [task for task in tasks.values() if task['column_id'] == column_id]
    for task in column_tasks:
        del tasks[task['id']]
    
    del columns[column_id]
    save_data()
    
    return jsonify({'message': 'Column deleted successfully'})

# 8. Task Routes
@app.route('/api/columns/<column_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(column_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    column = columns.get(column_id)
    if not column:
        return jsonify({'error': 'Column not found'}), 404
    
    board = boards.get(column['board_id'])
    if not board or board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description', '')
    
    if not title:
        return jsonify({'error': 'Task title is required'}), 400
    
    # Get the highest position in this column
    column_tasks = [task for task in tasks.values() if task['column_id'] == column_id]
    position = max([task.get('position', 0) for task in column_tasks], default=-1) + 1
    
    task_id = str(uuid.uuid4())
    task = {
        'id': task_id,
        'title': title,
        'description': description,
        'column_id': column_id,
        'position': position,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    tasks[task_id] = task
    save_data()
    
    return jsonify(task), 201

@app.route('/api/tasks/<task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    column = columns.get(task['column_id'])
    if not column:
        return jsonify({'error': 'Column not found'}), 404
    
    board = boards.get(column['board_id'])
    if not board or board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    column_id = data.get('column_id')
    position = data.get('position')
    
    if title:
        task['title'] = title
    
    if description is not None:
        task['description'] = description
    
    if column_id and column_id != task['column_id']:
        # Verify column exists and belongs to same board
        new_column = columns.get(column_id)
        if not new_column or new_column['board_id'] != board['id']:
            return jsonify({'error': 'Invalid column'}), 400
        
        task['column_id'] = column_id
    
    if position is not None:
        task['position'] = position
    
    task['updated_at'] = datetime.now().isoformat()
    save_data()
    
    return jsonify(task)

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    current_user = get_jwt_identity()
    user_id = users[current_user]['id']
    
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    column = columns.get(task['column_id'])
    if not column:
        return jsonify({'error': 'Column not found'}), 404
    
    board = boards.get(column['board_id'])
    if not board or board['owner_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    del tasks[task_id]
    save_data()
    
    return jsonify({'message': 'Task deleted successfully'})

# 9. Error Handlers
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400

@app.errorhandler(500)
def server_error(e):
    return jsonify(error=str(e)), 500

# Initialize data on startup
load_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5349')), debug=False)
