from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
import datetime
import mimetypes

# App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filestorage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    storage_quota = db.Column(db
    .Integer, default=1073741824)  # 1GB in bytes
    storage_used = db.Column(db.Integer, default=0)
    files = db.relationship('File', backref='owner', lazy=True)
    folders = db.relationship('Folder', backref='owner', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'storage_quota': self.storage_quota,
            'storage_used': self.storage_used
        }

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    files = db.relationship('File', backref='folder', lazy=True)
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat()
        }

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(64), nullable=True, unique=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'folder_id': self.folder_id,
            'user_id': self.user_id,
            'upload_date': self.upload_date.isoformat(),
            'is_public': self.is_public,
            'share_token': self.share_token
        }

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    # Validate input
    if not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing fields'}), 400
        
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Username or email already in use'}), 409
    
    # Create and save the user
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(username=data['username'], email=data['email'], password=hashed_pw)
    
    # Create root folder for user
    root_folder = Folder(name='root', user_id=user.id)
    
    db.session.add(user)
    db.session.add(root_folder)
    db.session.commit()
    
    # Generate token and return
    token = create_access_token(identity=user.id)
    return jsonify({'token': token, 'user': user.to_dict()}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    
    # Validate input
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'error': 'Missing fields'}), 400
    
    # Find user
    user = User.query.filter_by(username=data['username']).first()
    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate token and return
    token = create_access_token(identity=user.id)
    return jsonify({'token': token, 'user': user.to_dict()}), 200

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

# Folder Management Routes
@app.route('/api/folders', methods=['GET'])
@jwt_required()
def get_folders():
    user_id = get_jwt_identity()
    parent_id = request.args.get('parent_id', None)
    
    if parent_id:
        # Check if the folder belongs to user
        folder = Folder.query.filter_by(id=parent_id, user_id=user_id).first()
        if not folder:
            return jsonify({'error': 'Folder not found or access denied'}), 404
        folders = Folder.query.filter_by(parent_id=parent_id, user_id=user_id).all()
    else:
        # Get root level folders
        folders = Folder.query.filter_by(parent_id=None, user_id=user_id).all()
    
    return jsonify([folder.to_dict() for folder in folders]), 200

@app.route('/api/folders', methods=['POST'])
@jwt_required()
def create_folder():
    user_id = get_jwt_identity()
    data = request.json
    
    # Validate input
    if 'name' not in data:
        return jsonify({'error': 'Folder name is required'}), 400
    
    parent_id = data.get('parent_id')
    
    # If parent folder is specified, check if it exists and belongs to user
    if parent_id:
        parent = Folder.query.filter_by(id=parent_id, user_id=user_id).first()
        if not parent:
            return jsonify({'error': 'Parent folder not found or access denied'}), 404
    
    # Create folder
    folder = Folder(
        name=data['name'],
        user_id=user_id,
        parent_id=parent_id
    )
    
    db.session.add(folder)
    db.session.commit()
    
    return jsonify(folder.to_dict()), 201

@app.route('/api/folders/<int:folder_id>', methods=['PUT'])
@jwt_required()
def update_folder(folder_id):
    user_id = get_jwt_identity()
    folder = Folder.query.filter_by(id=folder_id, user_id=user_id).first()
    
    if not folder:
        return jsonify({'error': 'Folder not found or access denied'}), 404
    
    data = request.json
    
    # Update folder name if provided
    if 'name' in data:
        folder.name = data['name']
    
    # Update parent folder if provided
    if 'parent_id' in data:
        # Check if target parent folder exists and belongs to user
        if data['parent_id'] is not None:
            parent = Folder.query.filter_by(id=data['parent_id'], user_id=user_id).first()
            if not parent:
                return jsonify({'error': 'Parent folder not found or access denied'}), 404
        folder.parent_id = data['parent_id']
    
    db.session.commit()
    return jsonify(folder.to_dict()), 200

@app.route('/api/folders/<int:folder_id>', methods=['DELETE'])
@jwt_required()
def delete_folder(folder_id):
    user_id = get_jwt_identity()
    folder = Folder.query.filter_by(id=folder_id, user_id=user_id).first()
    
    if not folder:
        return jsonify({'error': 'Folder not found or access denied'}), 404
    
    # Cannot delete root folder
    root_folders = Folder.query.filter_by(parent_id=None, user_id=user_id).all()
    if folder in root_folders and len(root_folders) == 1:
        return jsonify({'error': 'Cannot delete the root folder'}), 400
    
    # Recursive delete of all contents
    def delete_recursive(folder_id):
        # Delete files in folder
        files = File.query.filter_by(folder_id=folder_id).all()
        for file in files:
            # Remove the physical file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Update user storage quota
            folder.owner.storage_used -= file.file_size
            
            # Remove from database
            db.session.delete(file)
        
        # Delete subfolders recursively
        subfolders = Folder.query.filter_by(parent_id=folder_id).all()
        for subfolder in subfolders:
            delete_recursive(subfolder.id)
            db.session.delete(subfolder)
    
    delete_recursive(folder.id)
    db.session.delete(folder)
    db.session.commit()
    
    return jsonify({'message': 'Folder and contents deleted successfully'}), 200

# File Management Routes
@app.route('/api/files', methods=['GET'])
@jwt_required()
def get_files():
    user_id = get_jwt_identity()
    folder_id = request.args.get('folder_id', None)
    file_type = request.args.get('file_type', None)
    
    query = File.query.filter_by(user_id=user_id)
    
    # Filter by folder if specified
    if folder_id:
        # Verify folder belongs to user
        folder = Folder.query.filter_by(id=folder_id, user_id=user_id).first()
        if not folder:
            return jsonify({'error': 'Folder not found or access denied'}), 404
        query = query.filter_by(folder_id=folder_id)
    
    # Filter by file type if specified
    if file_type:
        query = query.filter(File.file_type.like(f'{file_type}%'))
    
    files = query.all()
    return jsonify([file.to_dict() for file in files]), 200

@app.route('/api/files', methods=['POST'])
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get folder ID (root folder if not specified)
    folder_id = request.form.get('folder_id', None)
    if folder_id:
        folder = Folder.query.filter_by(id=folder_id, user_id=user_id).first()
        if not folder:
            return jsonify({'error': 'Folder not found or access denied'}), 404
    else:
        # Get user's root folder
        folder = Folder.query.filter_by(parent_id=None, user_id=user_id).first()
        folder_id = folder.id if folder else None
    
    # Check file size against user's quota
    file_size = len(file.read())
    file.seek(0)  # Reset file pointer after reading
    
    # Check if user has enough quota
    if user.storage_used + file_size > user.storage_quota:
        return jsonify({'error': 'Storage quota exceeded'}), 413
    
    # Generate a unique filename to avoid collisions
    original_filename = secure_filename(file.filename)
    file_ext = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Determine file type
    file_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
    
    # Save the file
    file.save(file_path)
    
    # Create database record
    new_file = File(
        filename=unique_filename,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size,
        folder_id=folder_id,
        user_id=user_id
    )
    
    # Update user's storage usage
    user.storage_used += file_size
    
    db.session.add(new_file)
    db.session.commit()
    
    return jsonify(new_file.to_dict()), 201

@app.route('/api/files/<int:file_id>', methods=['GET'])
@jwt_required(optional=True)
def download_file(file_id):
    # Get current user if authenticated
    current_user_id = get_jwt_identity()
    
    file = File.query.get(file_id)
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    # Check access permissions
    if not file.is_public and (current_user_id is None or file.user_id != current_user_id):
        return jsonify({'error': 'Access denied'}), 403
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on server'}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file.original_filename,
        mimetype=file.file_type
    )

@app.route('/api/files/<int:file_id>', methods=['PUT'])
@jwt_required()
def update_file(file_id):
    user_id = get_jwt_identity()
    file = File.query.filter_by(id=file_id, user_id=user_id).first()
    
    if not file:
        return jsonify({'error': 'File not found or access denied'}), 404
    
    data = request.json
    
    # Update file attributes
    if 'filename' in data:
        file.original_filename = data['filename']
    
    if 'is_public' in data:
        file.is_public = data['is_public']
        # Generate a share token if file is made public
        if data['is_public'] and not file.share_token:
            file.share_token = uuid.uuid4().hex
    
    if 'folder_id' in data:
        # Verify the target folder belongs to the user
        folder = Folder.query.filter_by(id=data['folder_id'], user_id=user_id).first()
        if not folder:
            return jsonify({'error': 'Target folder not found or access denied'}), 404
        file.folder_id = data['folder_id']
    
    db.session.commit()
    return jsonify(file.to_dict()), 200

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    file = File.query.filter_by(id=file_id, user_id=user_id).first()
    
    if not file:
        return jsonify({'error': 'File not found or access denied'}), 404
    
    # Delete the physical file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Update user's storage usage
    user.storage_used -= file.file_size
    
    # Delete database record
    db.session.delete(file)
    db.session.commit()
    
    return jsonify({'message': 'File deleted successfully'}), 200

# Shared File Routes
@app.route('/api/share/<share_token>', methods=['GET'])
def access_shared_file(share_token):
    file = File.query.filter_by(share_token=share_token, is_public=True).first()
    
    if not file:
        return jsonify({'error': 'Shared file not found or access denied'}), 404
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on server'}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file.original_filename,
        mimetype=file.file_type
    )

@app.route('/api/share', methods=['POST'])
@jwt_required()
def share_file():
    user_id = get_jwt_identity()
    data = request.json
    
    if 'file_id' not in data:
        return jsonify({'error': 'File ID is required'}), 400
    
    file = File.query.filter_by(id=data['file_id'], user_id=user_id).first()
    
    if not file:
        return jsonify({'error': 'File not found or access denied'}), 404
    
    # Make file public and generate token if not already
    file.is_public = True
    if not file.share_token:
        file.share_token = uuid.uuid4().hex
    
    db.session.commit()
    
    share_url = f"/api/share/{file.share_token}"
    return jsonify({
        'share_token': file.share_token,
        'share_url': share_url
    }), 200

@app.route('/api/share/<int:file_id>', methods=['DELETE'])
@jwt_required()
def unshare_file(file_id):
    user_id = get_jwt_identity()
    file = File.query.filter_by(id=file_id, user_id=user_id).first()
    
    if not file:
        return jsonify({'error': 'File not found or access denied'}), 404
    
    # Make file private and remove share token
    file.is_public = False
    file.share_token = None
    
    db.session.commit()
    
    return jsonify({'message': 'File is no longer shared'}), 200

# Storage Quota Management
@app.route('/api/quota', methods=['GET'])
@jwt_required()
def get_storage_info():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'quota': user.storage_quota,
        'used': user.storage_used,
        'available': user.storage_quota - user.storage_used,
        'percentage_used': (user.storage_used / user.storage_quota) * 100 if user.storage_quota > 0 else 0
    }), 200

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(413)
def payload_too_large(error):
    return jsonify({'error': 'File size exceeds the allowed limit'}), 413

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5347')))
