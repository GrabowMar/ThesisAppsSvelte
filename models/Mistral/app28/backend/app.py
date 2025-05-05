# 1. Imports Section
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 3. Database Models (if needed)
# 4. Authentication Logic (if needed)
# 5. Utility Functions
# 6. API Routes

@app.route('/api/upload', methods=['POST'])
def upload_artwork():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)

    return jsonify({"message": "File uploaded successfully", "filename": unique_filename}), 200

@app.route('/api/artworks', methods=['GET'])
def list_artworks():
    artworks = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify(artworks), 200

@app.route('/api/artworks/<filename>', methods=['GET'])
def get_artwork(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5135')))
