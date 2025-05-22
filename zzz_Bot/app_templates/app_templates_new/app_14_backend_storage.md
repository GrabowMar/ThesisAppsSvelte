# Backend Generation Prompt - Flask File Storage Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/files`, `/api/folders`, `/api/shares`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**File Storage System Backend**  
A comprehensive Flask backend for cloud storage application, featuring secure file management, folder organization, sharing capabilities, quota management, and access control with enterprise-grade security.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Secure file upload and download with validation
- Hierarchical folder organization and navigation
- File sharing with permission management
- Storage quota tracking and enforcement
- File type filtering and validation
- User authentication and access control
- File versioning and backup capabilities
- Bulk operations for multiple files
- Search and metadata management
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, send_file, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
from werkzeug.utils import secure_filename
import hashlib
import mimetypes
import magic
from pathlib import Path
import shutil

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'storage'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB per file
app.config['DEFAULT_QUOTA'] = 10 * 1024 * 1024 * 1024  # 10GB default

# 3. Database Models/Setup
# 4. File Management Logic
# 5. Quota Management
# 6. Sharing and Permissions
# 7. API Routes:
#    - POST /api/upload (upload files)
#    - GET /api/files (list files and folders)
#    - GET /api/files/<id> (get file details)
#    - GET /api/files/<id>/download (download file)
#    - PUT /api/files/<id> (update file metadata)
#    - DELETE /api/files/<id> (delete file)
#    - POST /api/folders (create folder)
#    - GET /api/folders/<id> (get folder contents)
#    - PUT /api/folders/<id> (update folder)
#    - DELETE /api/folders/<id> (delete folder)
#    - POST /api/files/<id>/share (create share link)
#    - GET /api/shares/<token> (access shared file)
#    - DELETE /api/shares/<id> (revoke share)
#    - GET /api/quota (get storage usage)
#    - GET /api/search (search files)
#    - POST /api/files/move (move files/folders)
#    - POST /api/files/copy (copy files/folders)
#    - GET /api/activity (get activity log)
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password
   - Validate input and create user account
   - Initialize user storage quota
   - Create user root folder
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and storage stats

3. **POST /api/auth/logout**
   - Clear user session
   - Log activity
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include storage usage and quota information

### File Management Routes

5. **POST /api/upload**
   - Accept multiple file uploads
   - Validate file types and sizes
   - Check storage quota before upload
   - Generate unique file identifiers
   - Store files with metadata
   - Update storage usage
   - Return upload results

6. **GET /api/files**
   - Return files and folders in specified directory
   - Accept: folder_id, sort, filter parameters
   - Support pagination for large directories
   - Include file metadata and permissions

7. **GET /api/files/<id>**
   - Return specific file details
   - Include metadata, sharing info, and statistics
   - Check user permissions

8. **GET /api/files/<id>/download**
   - Serve file for download
   - Validate user permissions
   - Log download activity
   - Support range requests for large files

9. **PUT /api/files/<id>**
   - Update file metadata
   - Accept: name, description, tags
   - Require appropriate permissions
   - Log modification activity

10. **DELETE /api/files/<id>**
    - Delete file and update storage usage
    - Move to trash with recovery option
    - Check user permissions
    - Clean up shares and references

### Folder Management Routes

11. **POST /api/folders**
    - Create new folder
    - Accept: name, parent_id, description
    - Validate permissions on parent folder
    - Return created folder info

12. **GET /api/folders/<id>**
    - Return folder contents
    - Include subfolders and files
    - Support sorting and filtering
    - Check user permissions

13. **PUT /api/folders/<id>**
    - Update folder metadata
    - Accept: name, description
    - Require appropriate permissions
    - Return updated folder info

14. **DELETE /api/folders/<id>**
    - Delete folder and all contents
    - Update storage usage calculations
    - Handle nested folder deletion
    - Check permissions recursively

### File Sharing Routes

15. **POST /api/files/<id>/share**
    - Create shareable link for file
    - Accept: permissions, expiry_date, password
    - Generate secure sharing token
    - Return share link and settings

16. **GET /api/shares/<token>**
    - Access shared file via token
    - Validate share permissions and expiry
    - Log access activity
    - Return file info or download

17. **DELETE /api/shares/<id>**
    - Revoke share link
    - Require file owner permissions
    - Clean up share metadata
    - Return confirmation

### Storage and Utility Routes

18. **GET /api/quota**
    - Return user storage usage statistics
    - Include quota limits and available space
    - Break down by file types
    - Include largest files and folders

19. **GET /api/search**
    - Search files and folders by name, content, metadata
    - Accept: query, file_type, date_range, folder_id
    - Support advanced search operators
    - Return ranked results

20. **POST /api/files/move**
    - Move files/folders to different location
    - Accept: item_ids, target_folder_id
    - Validate permissions on source and target
    - Update folder structures

21. **POST /api/files/copy**
    - Copy files/folders to different location
    - Accept: item_ids, target_folder_id
    - Check storage quota for copies
    - Return operation results

22. **GET /api/activity**
    - Return user activity log
    - Include file operations, shares, downloads
    - Support date filtering and pagination
    - Show activity statistics

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- created_at (TIMESTAMP)
- storage_quota (INTEGER)
- storage_used (INTEGER DEFAULT 0)
- is_active (BOOLEAN DEFAULT TRUE)

Files table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- folder_id (TEXT)
- name (TEXT NOT NULL)
- original_name (TEXT)
- file_path (TEXT NOT NULL)
- file_size (INTEGER)
- mime_type (TEXT)
- file_hash (TEXT)
- description (TEXT)
- tags (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- download_count (INTEGER DEFAULT 0)
- is_deleted (BOOLEAN DEFAULT FALSE)

Folders table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- parent_id (TEXT)
- name (TEXT NOT NULL)
- description (TEXT)
- path (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- file_count (INTEGER DEFAULT 0)
- total_size (INTEGER DEFAULT 0)
- is_deleted (BOOLEAN DEFAULT FALSE)

Shares table:
- id (TEXT PRIMARY KEY)
- file_id (TEXT)
- user_id (TEXT)
- share_token (TEXT UNIQUE)
- permission_level (TEXT) -- 'view', 'download'
- password_hash (TEXT)
- expires_at (TIMESTAMP)
- created_at (TIMESTAMP)
- access_count (INTEGER DEFAULT 0)
- is_active (BOOLEAN DEFAULT TRUE)

Activity_Log table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- action (TEXT) -- 'upload', 'download', 'delete', 'share', etc.
- target_id (TEXT) -- file or folder ID
- target_name (TEXT)
- ip_address (TEXT)
- user_agent (TEXT)
- created_at (TIMESTAMP)

File_Versions table:
- id (TEXT PRIMARY KEY)
- file_id (TEXT)
- version_number (INTEGER)
- file_path (TEXT)
- file_size (INTEGER)
- created_at (TIMESTAMP)
- is_current (BOOLEAN DEFAULT FALSE)
```

## File Storage Features

- **Hierarchical folder structure** with unlimited nesting
- **File versioning** with rollback capabilities
- **Duplicate detection** using file hashes
- **Storage optimization** with deduplication
- **Trash/recycle bin** with recovery options
- **Bulk operations** for multiple files and folders
- **File compression** for storage efficiency
- **Metadata extraction** and indexing

## Security and Access Control

- **User-based file isolation** and permissions
- **Secure file storage** outside web root
- **File type validation** using magic numbers
- **Virus scanning** integration (optional)
- **Access logging** for audit trails
- **Share link security** with tokens and expiry
- **Password protection** for sensitive shares
- **Rate limiting** for API operations

## Quota and Storage Management

- **Per-user storage quotas** with enforcement
- **Real-time usage tracking** and updates
- **Storage analytics** and reporting
- **Automatic cleanup** of deleted files
- **Storage optimization** recommendations
- **Quota alerts** and notifications
- **Admin quota management** capabilities

## Performance Optimization Features

- **Chunked file uploads** for large files
- **Resume uploads** for interrupted transfers
- **CDN integration** support
- **Caching strategies** for frequently accessed files
- **Database indexing** for fast queries
- **Asynchronous operations** for bulk tasks
- **File streaming** for large downloads

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, python-magic, file handling libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - File validation and security
   - Storage quota management
   - Share link security
   - Activity logging and monitoring
   - Performance optimization for large files
   - Backup and recovery capabilities
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all cloud storage scenarios including file management, sharing, quota enforcement, and security with proper validation and performance optimization.