# Imports Section
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import uuid

# App Configuration
app = Flask(__name__)
CORS(app)

# Create a folder for user data if it doesn't already exist
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Storage Quota (example: 100MB in bytes)
STORAGE_QUOTA = 100 * 1024 * 1024  # 100MB

# Helper Functions
def calculate_storage_used():
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(UPLOAD_FOLDER):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

# Routes Section

@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if not file:
        return jsonify({"error": "No file provided"}), 400

    # Calculate quota
    if calculate_storage_used() + len(file.read()) > STORAGE_QUOTA:
        return jsonify({"error": "Storage quota exceeded"}), 400
    
    # Reset file pointer and save
    file.seek(0)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    return jsonify({"message": "File uploaded successfully", "filename": file.filename}), 200

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/files', methods=['GET'])
def list_files():
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify({"files": files}), 200

@app.route('/api/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    os.remove(file_path)
    return jsonify({"message": "File deleted successfully"}), 200

@app.route('/api/quota', methods=['GET'])
def get_quota():
    storage_used = calculate_storage_used()
    return jsonify({"used": storage_used, "quota": STORAGE_QUOTA}), 200

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5267')))
