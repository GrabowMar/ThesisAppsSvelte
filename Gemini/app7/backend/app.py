from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import uuid

# App Configuration
app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create folder if it doesn't exist

# Allow only files up to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Utility Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API Routes
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handles file uploads."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = str(uuid.uuid4()) + '.' + file_extension # Generate unique filenames
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return jsonify({'message': 'File uploaded successfully', 'filename': unique_filename}), 201
    else:
        return jsonify({'error': 'Invalid file type or no file provided.'}), 400

@app.route('/api/files', methods=['GET'])
def list_files():
    """Lists all available files in the upload directory."""
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify(files), 200

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Downloads a specific file."""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_file(filename):
    """Serves a specific file for preview."""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

# Error Handlers
@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'error': 'File size too large. Maximum size is 16MB.'}), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5413, debug=True)
