# app.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
QUOTA = 100 * 1024 * 1024  # 100 MB

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Required pip dependencies
# requirements.txt
# Flask
# flask_cors

# In-memory storage for demonstration purposes
# Replace with a database in a production environment
files = {}

# Login and registration routes
@app.route('/login', methods=['POST'])
def login():
    # Implement login logic
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/register', methods=['POST'])
def register():
    # Implement registration logic
    return jsonify({'message': 'Registered successfully'}), 200

# File upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'message': 'No file part'}), 400
        file = request.files['file']
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
        if file:
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            files[file_id] = {
                'filename': filename,
                'size': os.path.getsize(file),
                'type': file.mimetype
            }
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_id))
            return jsonify({'message': 'File uploaded successfully'}), 200

# File download route
@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    if file_id in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        return send_file(file_path, as_attachment=True)
    return jsonify({'message': 'File not found'}), 404

# File sharing route
@app.route('/share/<file_id>', methods=['GET'])
def share_file(file_id):
    if file_id in files:
        # Implement file sharing logic
        return jsonify({'message': 'File shared successfully'}), 200
    return jsonify({'message': 'File not found'}), 404

# Storage quota management route
@app.route('/quota', methods=['GET'])
def get_quota():
    used_quota = sum(files[file_id]['size'] for file_id in files)
    return jsonify({'quota': QUOTA, 'used': used_quota}), 200

# File type filtering route
@app.route('/files/<file_type>', methods=['GET'])
def get_files_by_type(file_type):
    filtered_files = {file_id: file for file_id, file in files.items() if file['type'] == file_type}
    return jsonify(filtered_files), 200

if __name__ == '__main__':
    app.run(port=5027)
