# 1. Imports Section
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 3. Database Models (if needed)
# For simplicity, we'll use in-memory storage. In a production app, use a database.
galleries = {}
images = {}

# 4. Authentication Logic (if needed)
# For simplicity, we'll use a basic authentication system.
users = {'admin': 'password123'}

def authenticate(username, password):
    return users.get(username) == password

# 5. Utility Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if authenticate(data.get('username'), data.get('password')):
        return jsonify({'message': 'Logged in successfully'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username in users:
        return jsonify({'message': 'Username already exists'}), 400
    users[username] = password
    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/api/galleries', methods=['GET', 'POST'])
def manage_galleries():
    if request.method == 'POST':
        data = request.json
        gallery_id = str(uuid.uuid4())
        galleries[gallery_id] = {'name': data['name'], 'images': []}
        return jsonify({'id': gallery_id, 'name': data['name']}), 201
    return jsonify(list(galleries.values())), 200

@app.route('/api/galleries/<gallery_id>/images', methods=['GET', 'POST'])
def manage_gallery_images(gallery_id):
    if gallery_id not in galleries:
        return jsonify({'message': 'Gallery not found'}), 404
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'message': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_id = str(uuid.uuid4())
            images[image_id] = {'filename': filename, 'metadata': request.form.to_dict()}
            galleries[gallery_id]['images'].append(image_id)
            return jsonify({'id': image_id, 'filename': filename}), 201
        return jsonify({'message': 'Invalid file type'}), 400
    
    gallery_images = [{'id': img_id, 'filename': images[img_id]['filename']} for img_id in galleries[gallery_id]['images']]
    return jsonify(gallery_images), 200

@app.route('/api/images/<image_id>', methods=['GET'])
def get_image(image_id):
    if image_id not in images:
        return jsonify({'message': 'Image not found'}), 404
    return jsonify({'id': image_id, 'filename': images[image_id]['filename'], 'metadata': images[image_id]['metadata']}), 200

@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found', 'error': str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error', 'error': str(error)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6005')))
