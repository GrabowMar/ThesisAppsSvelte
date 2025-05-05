# 1. Imports Section
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import uuid
import datetime
import mimetypes
from werkzeug.utils import secure_filename

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Maximum file size (16 MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 3. Database Models - Using file-based storage for simplicity
# In a production app, use a proper database

# 5. Utility Functions
def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(directory, filename):
    """Get file metadata"""
    file_path = os.path.join(directory, filename)
    stats = os.stat(file_path)
    
    # Determine file type
    file_type, _ = mimetypes.guess_type(file_path)
    if file_type is None:
        file_type = "application/octet-stream"
    
    # Get file extension for icon selection
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ""
    
    return {
        'id': filename,
        'name': filename,
        'size': stats.st_size,
        'type': file_type,
        'extension': extension,
        'uploadDate': datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'url': f"/api/files/{filename}"
    }
    
def list_files():
    """List all files in the upload directory with metadata"""
    files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                files.append(get_file_info(app.config['UPLOAD_FOLDER'], filename))
    return files

# 6. API Routes
@app.route('/api/healthcheck', methods=['GET'])
def healthcheck():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Service is running"}), 200

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get list of all uploaded files"""
    try:
        files = list_files()
        return jsonify({"files": files}), 200
    except Exception as e:
        app.logger.error(f"Error listing files: {str(e)}")
        return jsonify({"error": "Failed to list files"}), 500

@app.route('/api/files', methods=['POST'])
def upload_file():
    """Upload a new file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400
    
    try:
        # Secure the filename and make it unique
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(file_path)
        
        # Return the file info
        file_info = get_file_info(app.config['UPLOAD_FOLDER'], unique_filename)
        return jsonify({"message": "File uploaded successfully", "file": file_info}), 201
    
    except Exception as e:
        app.logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": "Failed to upload file"}), 500

@app.route('/api/files/<filename>', methods=['GET'])
def download_file(filename):
    """Download a specific file"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        return jsonify({"error": "Failed to download file"}), 500

@app.route('/api/files/preview/<filename>', methods=['GET'])
def preview_file(filename):
    """Preview a file (without downloading)"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        app.logger.error(f"Error previewing file: {str(e)}")
        return jsonify({"error": "Failed to preview file"}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a specific file"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"message": "File deleted successfully"}), 200
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        app.logger.error(f"Error deleting file: {str(e)}")
        return jsonify({"error": "Failed to delete file"}), 500

# 7. Error Handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large. Maximum file size is 16MB"}), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5333')), debug=True)