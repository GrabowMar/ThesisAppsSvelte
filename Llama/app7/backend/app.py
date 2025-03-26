# 1. Imports Section
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# For simplicity, we will use a dictionary to store file metadata
files = {}

# 4. Authentication Logic (if needed)
# No authentication is required for this example

# 5. Utility Functions
def generate_file_id():
    return str(uuid.uuid4())

# 6. API Routes
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    file_id = generate_file_id()
    file.save(os.path.join('uploads', file_id))
    files[file_id] = file.filename
    return jsonify({'file_id': file_id})

@app.route('/api/files', methods=['GET'])
def list_files():
    return jsonify([{'file_id': file_id, 'filename': filename} for file_id, filename in files.items()])

@app.route('/api/download/<file_id>', methods=['GET'])
def download_file(file_id):
    if file_id not in files:
        return jsonify({'error': 'File not found'}), 404
    return send_file(os.path.join('uploads', file_id), as_attachment=True)

@app.route('/api/preview/<file_id>', methods=['GET'])
def preview_file(file_id):
    if file_id not in files:
        return jsonify({'error': 'File not found'}), 404
    with open(os.path.join('uploads', file_id), 'rb') as file:
        return jsonify({'filename': files[file_id], 'content': file.read().decode('utf-8')})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5013')))
