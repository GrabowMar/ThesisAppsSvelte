from flask import Flask, request, jsonify, send_from_directory, abort
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "uploads"
SHARED_FOLDER = "shared"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
MAX_STORAGE_QUOTA = 100 * 1024 * 1024  # 100MB

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SHARED_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_storage():
    """Calculate total storage used."""
    total_size = sum(os.path.getsize(os.path.join(UPLOAD_FOLDER, f)) for f in os.listdir(UPLOAD_FOLDER))
    return total_size

@app.route("/upload", methods=["POST"])
def upload_file():
    """Upload a file to the server."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # Check storage quota
    file_size = request.content_length
    if calculate_storage() + file_size > MAX_STORAGE_QUOTA:
        return jsonify({"error": "Storage quota exceeded"}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return jsonify({"message": "File uploaded successfully", "filename": filename}), 200

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """Download a file from the server."""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route("/share/<filename>", methods=["POST"])
def share_file(filename):
    """Share a file by copying it to the shared folder."""
    source_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(source_path):
        return jsonify({"error": "File not found"}), 404
    shared_path = os.path.join(SHARED_FOLDER, filename)
    os.rename(source_path, shared_path)
    return jsonify({"message": "File shared successfully"}), 200

@app.route("/files", methods=["GET"])
def list_files():
    """List all uploaded files."""
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify({"files": files}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5187)
