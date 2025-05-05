# 1. Imports Section
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import os
import uuid  # For generating unique filenames
import hashlib  # For secure password hashing (if implementing user accounts)
import secrets  # For generating secure random tokens
import mimetypes

# 2. App Configuration
app = Flask(__name__, static_folder='uploads')  # Serve uploads directory
CORS(app)  # Enable CORS for all routes

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'doc', 'docx', 'xls', 'xlsx'}  # Example file types
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB Limit (adjust as needed)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create the upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Example storage quota (in bytes)
STORAGE_QUOTA = 100 * 1024 * 1024  # 100MB

# In-memory storage for quota tracking (replace with a database in production)
current_storage_usage = 0


# 3. Database Models (if needed) -  Skipping for simplicity, use SQLAlchemy in real app

# 4. Authentication Logic (if needed) - Skipping for simplicity, use Flask-Login/JWT in real app

# 5. Utility Functions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_quota(file_size):
    global current_storage_usage
    if (current_storage_usage + file_size) > STORAGE_QUOTA:
        return False
    return True

def update_quota(file_size):
    global current_storage_usage
    current_storage_usage += file_size

def reduce_quota(file_size):
    global current_storage_usage
    current_storage_usage -= file_size

# 6. API Routes

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + "_" + file.filename  # Secure filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0) # Reset cursor position

        if not check_quota(file_size):
            return jsonify({'message': 'Storage quota exceeded'}), 413

        file.save(filepath)
        update_quota(file_size)

        return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 201
    else:
        return jsonify({'message': 'Invalid file type'}), 400


@app.route('/api/files', methods=['GET'])
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_data = []
    for filename in files:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_size = os.path.getsize(filepath)
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'  # Guessed MIME type
        file_data.append({'filename': filename, 'size': file_size, 'mime_type': mime_type})
    return jsonify(file_data), 200

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        file_size = os.path.getsize(filepath)
        os.remove(filepath)
        reduce_quota(file_size)
        return jsonify({'message': 'File deleted successfully'}), 200
    except FileNotFoundError:
        return jsonify({'message': 'File not found'}), 404
    except OSError as e:
        return jsonify({'message': f'Error deleting file: {str(e)}'}), 500

@app.route('/api/quota', methods=['GET'])
def get_quota():
    global current_storage_usage
    return jsonify({'used': current_storage_usage, 'total': STORAGE_QUOTA}), 200

# Example route for future use (demonstrates multipage routing concept)
@app.route('/api/about', methods=['GET'])
def about():
  return jsonify({"message": "About this file storage app."}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(413)
def too_large(error):
    return jsonify({'message': 'Request Entity Too Large: File size exceeds the limit.'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5427, debug=True)
