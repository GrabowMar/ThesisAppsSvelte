from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
STORAGE_QUOTA = 1 * 1024 * 1024 * 1024  # 1 GB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_storage_used():
    return sum(os.path.getsize(os.path.join(UPLOAD_FOLDER, f)) for f in os.listdir(UPLOAD_FOLDER))

# Routes
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400
    if file.content_length > MAX_FILE_SIZE:
        return jsonify({"error": "File size exceeds limit"}), 400
    if get_storage_used() + file.content_length > STORAGE_QUOTA:
        return jsonify({"error": "Storage quota exceeded"}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({"message": "File uploaded successfully", "filename": filename}), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, as_attachment=True)

@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify({"files": files}), 200

@app.route('/storage', methods=['GET'])
def get_storage_info():
    used = get_storage_used()
    return jsonify({"used": used, "quota": STORAGE_QUOTA}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5189)  # Replace with your backend port

