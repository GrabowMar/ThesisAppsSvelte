# Backend Generation Prompt - Flask File Uploader Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper security.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/upload`, `/api/files`, `/api/download`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**File Uploader System Backend**  
A comprehensive Flask backend for file upload application, featuring secure file handling, storage management, download capabilities, file organization, and preview generation.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Secure file upload with validation and size limits
- File listing and metadata management
- Download functionality with access control
- File preview generation for supported formats
- File organization with folders/categories
- File search and filtering capabilities
- Storage management and cleanup
- CORS support for frontend communication
- Database integration for file metadata

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, send_file, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import hashlib
from PIL import Image
import magic

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['UPLOAD_FOLDER'] = 'uploads'

# 3. Database Models/Setup
# 4. File Validation Logic
# 5. File Processing (thumbnails, previews)
# 6. Storage Management
# 7. API Routes:
#    - POST /api/upload (upload files)
#    - GET /api/files (list files with pagination/filtering)
#    - GET /api/files/<id> (get file metadata)
#    - GET /api/files/<id>/download (download file)
#    - GET /api/files/<id>/preview (get file preview/thumbnail)
#    - DELETE /api/files/<id> (delete file)
#    - POST /api/folders (create folder)
#    - GET /api/folders (list folders)
#    - PUT /api/files/<id>/move (move file to folder)
#    - GET /api/search (search files)
#    - GET /api/storage/stats (storage statistics)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### File Upload Routes

1. **POST /api/upload**
   - Accept multiple file uploads
   - Validate file types and sizes
   - Generate unique filenames and IDs
   - Store file metadata in database
   - Create thumbnails for images
   - Return upload confirmation with file IDs

### File Management Routes

2. **GET /api/files**
   - Return paginated list of uploaded files
   - Support filtering by type, folder, date range
   - Include file metadata (size, type, upload date)
   - Support sorting by various criteria

3. **GET /api/files/<id>**
   - Return detailed file metadata
   - Include file statistics and access history
   - Check file existence and integrity

4. **GET /api/files/<id>/download**
   - Serve file for download
   - Implement access control if needed
   - Log download activity
   - Support resume/partial downloads

5. **GET /api/files/<id>/preview**
   - Generate and serve file previews
   - Support image thumbnails
   - Handle text file previews
   - Return appropriate preview format

6. **DELETE /api/files/<id>**
   - Delete file from storage and database
   - Implement soft delete with recovery option
   - Clean up associated thumbnails/previews
   - Return confirmation response

### Folder Management Routes

7. **POST /api/folders**
   - Create new folder/category
   - Accept: name, description, parent_folder_id
   - Validate folder structure
   - Return created folder info

8. **GET /api/folders**
   - Return folder structure
   - Include file counts for each folder
   - Support nested folder hierarchies

9. **PUT /api/files/<id>/move**
   - Move file to different folder
   - Accept: target_folder_id
   - Update file metadata
   - Return updated file info

### Search and Statistics Routes

10. **GET /api/search**
    - Search files by name, type, content
    - Accept: query, file_type, folder, date_range
    - Return ranked search results
    - Support advanced search operators

11. **GET /api/storage/stats**
    - Return storage usage statistics
    - Include total size, file counts by type
    - Storage usage by folder
    - Recent activity summary

## Database Schema

```sql
Files table:
- id (TEXT PRIMARY KEY)
- original_name (TEXT NOT NULL)
- stored_name (TEXT NOT NULL)
- file_path (TEXT NOT NULL)
- mime_type (TEXT)
- file_size (INTEGER)
- file_hash (TEXT)
- folder_id (INTEGER)
- uploaded_at (TIMESTAMP)
- last_accessed (TIMESTAMP)
- download_count (INTEGER DEFAULT 0)
- is_deleted (BOOLEAN DEFAULT FALSE)

Folders table:
- id (INTEGER PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- parent_id (INTEGER)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

File_Previews table:
- file_id (TEXT)
- preview_type (TEXT) -- thumbnail, text_preview, etc.
- preview_path (TEXT)
- created_at (TIMESTAMP)

Upload_Sessions table:
- id (TEXT PRIMARY KEY)
- session_id (TEXT)
- files_uploaded (INTEGER)
- total_size (INTEGER)
- started_at (TIMESTAMP)
- completed_at (TIMESTAMP)
```

## File Processing Features

- **File validation** with whitelist/blacklist of allowed types
- **Virus scanning** integration (optional)
- **Image processing** for thumbnail generation
- **Text extraction** for search indexing
- **File compression** for storage optimization
- **Duplicate detection** using file hashes
- **Metadata extraction** (EXIF for images, etc.)

## Security Features

- **File type validation** using both extension and magic numbers
- **File size limits** per file and per session
- **Filename sanitization** to prevent path traversal
- **Access control** for file downloads
- **Rate limiting** for upload operations
- **Malware scanning** capabilities
- **Secure file storage** outside web root
- **Upload session tracking** to prevent abuse

## Storage Management

- **Disk space monitoring** and cleanup
- **Automatic cleanup** of orphaned files
- **File archiving** for old/unused files
- **Storage quotas** per user/session
- **Backup and recovery** capabilities
- **File integrity checks** using checksums

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, Pillow, python-magic, etc.

3. **Production Ready Features**
   - Comprehensive error handling
   - File validation and security
   - Storage management and cleanup
   - Upload progress tracking
   - File integrity verification
   - Access logging and monitoring
   - Performance optimization for large files
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all file upload scenarios including security validation, storage management, preview generation, and download functionality with proper error handling and performance optimization.