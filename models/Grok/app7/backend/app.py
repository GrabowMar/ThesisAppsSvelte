# 1. Imports Section
from flask import Flask, jsonify, request, send_file, abort
from flask_cors import CORS
import os
import uuid
import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 5. Utility Functions
def save_file(file):
    """Save uploaded file to the server."""
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join('uploads', filename)
    file.save(file_path)
    return filename, file_path

def get_file_list():
    """Get list of files in the uploads directory."""
    files = os.listdir('uploads')
    return [{'name': f, 'size': os.path.getsize(os.path.join('uploads', f)), 'uploaded_at': datetime.datetime.fromtimestamp(os.path.getctime(os.path.join('uploads', f))).isoformat()} for f in files]

# 6. API Routes
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename, file_path = save_file(file)
    return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 200

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all uploaded files."""
    files = get_file_list()
    return jsonify(files), 200

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a specific file."""
    file_path = os.path.join('uploads', filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, as_attachment=True)

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_file(filename):
    """Preview a specific file."""
    file_path = os.path.join('uploads', filename)
    if not os.path.exists(file_path):
        abort(404)
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        return send_file(file_path, mimetype='image/' + filename.split('.')[-1])
    else:
        return jsonify({'error': 'Preview not supported for this file type'}), 400

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5993')))
