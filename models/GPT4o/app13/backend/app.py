# Imports Section
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import json

# App Configuration
app = Flask(__name__)
CORS(app)

# Configurations for image upload
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Utility function to check allowed file types."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/api/images', methods=["GET"])
def list_images():
    """Endpoint to list all uploaded images with metadata."""
    images = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            images.append({
                "name": filename,
                "url": f"http://localhost:5265/api/uploads/{filename}"
            })
    return jsonify(images), 200

@app.route('/api/images', methods=["POST"])
def upload_image():
    """Endpoint to upload an image."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return jsonify({"success": "File uploaded successfully", "filename": filename}), 201

    return jsonify({"error": "Unsupported file type"}), 400

@app.route('/api/uploads/<filename>', methods=["GET"])
def get_uploaded_image(filename):
    """Endpoint to serve uploaded image files."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    """Custom handler for 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    """Custom handler for server errors."""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5265)
