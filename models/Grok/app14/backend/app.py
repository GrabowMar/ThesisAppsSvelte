# 1. Imports Section
from flask import Flask, jsonify, request, send_file, abort
from flask_cors import CORS
import os
import jwt
import datetime
from functools import wraps
import uuid
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 3. Database Models (using in-memory storage for simplicity)
users = {}
files = {}
folders = {}

# 4. Authentication Logic
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = users.get(data['public_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# 5. Utility Functions
def save_file(file, user_id, folder_id=None):
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    file_id = str(uuid.uuid4())
    files[file_id] = {
        'id': file_id,
        'name': file.filename,
        'path': file_path,
        'user_id': user_id,
        'folder_id': folder_id,
        'size': os.path.getsize(file_path)
    }
    return file_id

def get_user_storage_usage(user_id):
    return sum(file['size'] for file in files.values() if file['user_id'] == user_id)

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if data.get('username') in users:
        return jsonify({'message': 'User already exists!'}), 400
    user_id = str(uuid.uuid4())
    users[user_id] = {
        'public_id': user_id,
        'username': data['username'],
        'password': data['password'],  # In a real app, you'd hash this
        'storage_quota': 1024 * 1024 * 1024  # 1GB
    }
    return jsonify({'message': 'User created successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401
    user = next((user for user in users.values() if user['username'] == auth.username), None)
    if not user or user['password'] != auth.password:
        return jsonify({'message': 'Could not verify'}), 401
    token = jwt.encode({'public_id': user['public_id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
    return jsonify({'token': token})

@app.route('/api/files', methods=['POST'])
@token_required
def upload_file(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected for uploading'}), 400
    if file:
        folder_id = request.form.get('folder_id')
        file_id = save_file(file, current_user['public_id'], folder_id)
        return jsonify({'message': 'File successfully uploaded', 'file_id': file_id}), 201
    else:
        return jsonify({'message': 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'}), 400

@app.route('/api/files/<file_id>', methods=['GET'])
@token_required
def download_file(current_user, file_id):
    file = files.get(file_id)
    if not file or file['user_id'] != current_user['public_id']:
        return jsonify({'message': 'File not found or unauthorized'}), 404
    return send_file(file['path'], as_attachment=True, attachment_filename=file['name'])

@app.route('/api/files', methods=['GET'])
@token_required
def list_files(current_user):
    user_files = [file for file in files.values() if file['user_id'] == current_user['public_id']]
    return jsonify(user_files), 200

@app.route('/api/folders', methods=['POST'])
@token_required
def create_folder(current_user):
    data = request.get_json()
    folder_id = str(uuid.uuid4())
    folders[folder_id] = {
        'id': folder_id,
        'name': data['name'],
        'user_id': current_user['public_id'],
        'parent_id': data.get('parent_id')
    }
    return jsonify({'message': 'Folder created successfully', 'folder_id': folder_id}), 201

@app.route('/api/folders', methods=['GET'])
@token_required
def list_folders(current_user):
    user_folders = [folder for folder in folders.values() if folder['user_id'] == current_user['public_id']]
    return jsonify(user_folders), 200

@app.route('/api/storage', methods=['GET'])
@token_required
def get_storage_info(current_user):
    used = get_user_storage_usage(current_user['public_id'])
    quota = current_user['storage_quota']
    return jsonify({
        'used': used,
        'quota': quota,
        'percentage': (used / quota) * 100 if quota > 0 else 0
    }), 200

@app.route('/api/share/<file_id>', methods=['POST'])
@token_required
def share_file(current_user, file_id):
    file = files.get(file_id)
    if not file or file['user_id'] != current_user['public_id']:
        return jsonify({'message': 'File not found or unauthorized'}), 404
    share_token = jwt.encode({'file_id': file_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)}, app.config['SECRET_KEY'])
    return jsonify({'share_token': share_token}), 200

@app.route('/api/share/<share_token>', methods=['GET'])
def get_shared_file(share_token):
    try:
        data = jwt.decode(share_token, app.config['SECRET_KEY'], algorithms=["HS256"])
        file = files.get(data['file_id'])
        if not file:
            return jsonify({'message': 'File not found'}), 404
        return send_file(file['path'], as_attachment=True, attachment_filename=file['name'])
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Share link has expired'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid share token'}), 400

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'message': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6007')))
