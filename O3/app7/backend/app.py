# 1. Imports Section
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 3. API Routes

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload endpoint. Expects a file in the 'file' form field.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Please select a file"}), 400

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return jsonify({"message": f"File '{file.filename}' uploaded successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """
    List all uploaded files.
    """
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        return jsonify({"files": files}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """
    Download file endpoint with content-disposition header set for attachment.
    """
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        abort(404, description=f"File '{filename}' not found")

@app.route('/api/preview/<path:filename>', methods=['GET'])
def preview_file(filename):
    """
    Preview file endpoint. For most files, the browser will try to display the file inline.
    """
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        abort(404, description=f"File '{filename}' not found")

# 7. Error Handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

# 8. Main Entrypoint
if __name__ == '__main__':
    # Use port 6153 for backend (per configuration)
    port = int(os.getenv('PORT', '6153'))
    app.run(host='0.0.0.0', port=port)
