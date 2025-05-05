# app/backend/app.py

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Directory for uploaded artworks
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- API Routes ---

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Upload artwork
@app.route('/api/upload', methods=['POST'])
def upload_artwork():
    if 'artwork' not in request.files:
        return jsonify({"error": "No artwork file uploaded"}), 400

    file = request.files['artwork']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return jsonify({"message": "Artwork uploaded successfully", "filename": file.filename}), 201

# List uploaded artworks
@app.route('/api/artworks', methods=['GET'])
def list_artworks():
    artworks = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify({"artworks": artworks}), 200

# Serve a specific artwork
@app.route('/api/artworks/<filename>', methods=['GET'])
def serve_artwork(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Error handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5795)
