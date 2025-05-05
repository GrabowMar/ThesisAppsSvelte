# Backend Logic
from flask import Flask, jsonify, request, send_from_directory, safe_join
from flask_cors import CORS
import os

UPLOAD_FOLDER = 'uploaded_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask App
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Utility: List Files in the Upload Directory
def list_uploaded_files():
    try:
        return os.listdir(app.config['UPLOAD_FOLDER'])
    except Exception as e:
        return []

# Routes
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = file.filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({'message': f'File {filename} uploaded successfully'}), 200

@app.route('/api/files', methods=['GET'])
def get_files():
    files = list_uploaded_files()
    return jsonify({'files': files})

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        safe_path = safe_join(app.config['UPLOAD_FOLDER'], filename)
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_file(filename):
    try:
        safe_path = safe_join(app.config['UPLOAD_FOLDER'], filename)
        with open(safe_path, 'r') as file:
            content = file.read()
            return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': 'Unable to preview file', 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5253)
