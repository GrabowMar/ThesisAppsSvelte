# 1. Imports
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import timedelta
import uuid

# 2. App Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage.db'
app.config['JWT_SECRET_KEY'] = os.urandom(24)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['UPLOAD_FOLDER'] = 'user_uploads'
app.config['MAX_STORAGE'] = 100 * 1024 * 1024  # 100MB default quota
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
CORS(app, supports_credentials=True)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    used_storage = db.Column(db.Integer, default=0)
    storage_quota = db.Column(db.Integer, default=app.config['MAX_STORAGE'])

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_folder = db.Column(db.Boolean, default=False)

class ShareToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

# 4. Utility Functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_user_dir(user_id):
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

# 5. Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 400

    user = User(
        username=data['username'],
        password_hash=generate_password_hash(data['password']),
        storage_quota=data.get('storage_quota', app.config['MAX_STORAGE'])
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({"msg": "Invalid credentials"}), 401
        
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

# 6. File Management Routes
@app.route('/api/files', methods=['GET'])
@jwt_required()
def list_files():
    user_id = get_jwt_identity()
    path = request.args.get('path', '')
    files = File.query.filter_by(user_id=user_id, path=path).all()
    return jsonify([{
        'id': f.id,
        'name': f.filename,
        'size': f.size,
        'is_folder': f.is_folder,
        'path': f.path
    } for f in files])

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if 'file' not in request.files:
        return jsonify({"msg": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"msg": "File type not allowed"}), 400

    filename = secure_filename(file.filename)
    file_path = request.form.get('path', '')
    user_dir = get_user_dir(user_id)
    
    file_size = request.content_length
    if user.used_storage + file_size > user.storage_quota:
        return jsonify({"msg": "Storage quota exceeded"}), 400

    save_path = os.path.join(user_dir, file_path, filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)
    
    new_file = File(
        filename=filename,
        path=file_path,
        size=file_size,
        user_id=user_id
    )
    db.session.add(new_file)
    user.used_storage += file_size
    db.session.commit()
    
    return jsonify({"msg": "File uploaded successfully"}), 201

# 7. Share Routes
@app.route('/api/share/<int:file_id>', methods=['POST'])
@jwt_required()
def generate_share_link(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != get_jwt_identity():
        return jsonify({"msg": "Unauthorized"}), 403
        
    token = str(uuid.uuid4()).replace('-', '')
    new_token = ShareToken(token=token, file_id=file_id, expires=datetime.utcnow() + timedelta(days=7))
    db.session.add(new_token)
    db.session.commit()
    
    return jsonify({"share_url": f"/shared/{token}"}), 200

@app.route('/shared/<token>', methods=['GET'])
def shared_file(token):
    share_token = ShareToken.query.filter_by(token=token).first_or_404()
    file = File.query.get_or_404(share_token.file_id)
    return send_from_directory(
        os.path.join(app.config['UPLOAD_FOLDER'], str(file.user_id)),
        os.path.join(file.path, file.filename)
    )

# 8. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"msg": "Resource not found"}), 404

# Initialize Database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5587')))
