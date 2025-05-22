# Backend Generation Prompt - Flask Gallery Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/images`, `/api/albums`, `/api/upload`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Gallery System Backend**  
A comprehensive Flask backend for gallery application, featuring image upload, processing, organization, metadata management, and album creation with security and performance optimization.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Secure image upload with validation and processing
- Gallery organization with albums and collections
- Image viewing with multiple resolution serving
- Comprehensive metadata extraction and storage
- Image search and filtering capabilities
- User authentication and gallery permissions
- Image optimization and thumbnail generation
- Batch operations for multiple images
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, send_file, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags
import hashlib
import mimetypes
import magic

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads/images'
app.config['THUMBNAIL_FOLDER'] = 'uploads/thumbnails'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# 3. Database Models/Setup
# 4. Image Processing Logic
# 5. Metadata Extraction
# 6. File Management
# 7. API Routes:
#    - POST /api/upload (upload images)
#    - GET /api/images (list images with pagination/filtering)
#    - GET /api/images/<id> (get specific image)
#    - PUT /api/images/<id> (update image metadata)
#    - DELETE /api/images/<id> (delete image)
#    - GET /api/images/<id>/download (download original)
#    - GET /api/images/<id>/thumbnail (get thumbnail)
#    - GET /api/albums (list albums)
#    - POST /api/albums (create album)
#    - PUT /api/albums/<id> (update album)
#    - DELETE /api/albums/<id> (delete album)
#    - POST /api/albums/<id>/images (add images to album)
#    - DELETE /api/albums/<id>/images/<image_id> (remove from album)
#    - GET /api/search (search images)
#    - GET /api/tags (get all tags)
#    - POST /api/images/batch (batch operations)
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
   - Hash password securely
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include gallery statistics and preferences

### Image Upload and Management Routes

5. **POST /api/upload**
   - Accept multiple image files
   - Validate file types and sizes
   - Generate thumbnails and optimized versions
   - Extract EXIF metadata
   - Store images with unique identifiers
   - Return upload results with image IDs

6. **GET /api/images**
   - Return paginated list of images
   - Support filtering by album, date, tags, user
   - Support sorting by date, name, size, views
   - Include thumbnail URLs and metadata

7. **GET /api/images/<id>**
   - Return specific image with full details
   - Include metadata, EXIF data, and statistics
   - Track view count and access history

8. **PUT /api/images/<id>**
   - Update image metadata
   - Accept: title, description, tags, album_id
   - Require authentication and ownership
   - Return updated image data

9. **DELETE /api/images/<id>**
   - Delete image and associated files
   - Remove thumbnails and processed versions
   - Update album associations
   - Require authentication and ownership

10. **GET /api/images/<id>/download**
    - Serve original image file
    - Track download statistics
    - Support range requests for large files

11. **GET /api/images/<id>/thumbnail**
    - Serve thumbnail image
    - Support multiple thumbnail sizes
    - Generate on-demand if not exists

### Album Management Routes

12. **GET /api/albums**
    - Return list of albums
    - Include image counts and cover images
    - Support filtering by user and privacy

13. **POST /api/albums**
    - Create new album
    - Accept: name, description, privacy_setting
    - Require authentication
    - Return created album

14. **PUT /api/albums/<id>**
    - Update album details
    - Accept: name, description, privacy_setting, cover_image_id
    - Require authentication and ownership
    - Return updated album

15. **DELETE /api/albums/<id>**
    - Delete album
    - Handle images (keep or delete based on settings)
    - Require authentication and ownership

16. **POST /api/albums/<id>/images**
    - Add images to album
    - Accept: image_ids array
    - Validate image ownership
    - Return updated album

17. **DELETE /api/albums/<id>/images/<image_id>**
    - Remove image from album
    - Keep original image unless specified
    - Return confirmation

### Search and Discovery Routes

18. **GET /api/search**
    - Search images by title, description, tags
    - Accept: query, filters (date, album, user)
    - Support advanced search operators
    - Return ranked results with metadata

19. **GET /api/tags**
    - Return list of all tags used
    - Include usage counts
    - Support tag autocomplete

20. **POST /api/images/batch**
    - Batch operations on multiple images
    - Accept: operation (delete, move, tag), image_ids
    - Process operations atomically
    - Return operation results

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- created_at (TIMESTAMP)
- total_images (INTEGER DEFAULT 0)
- storage_used (INTEGER DEFAULT 0)
- is_verified (BOOLEAN DEFAULT FALSE)

Images table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- filename (TEXT NOT NULL)
- original_filename (TEXT)
- file_path (TEXT NOT NULL)
- thumbnail_path (TEXT)
- file_size (INTEGER)
- image_width (INTEGER)
- image_height (INTEGER)
- mime_type (TEXT)
- file_hash (TEXT)
- title (TEXT)
- description (TEXT)
- uploaded_at (TIMESTAMP)
- view_count (INTEGER DEFAULT 0)
- download_count (INTEGER DEFAULT 0)

Albums table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT NOT NULL)
- description (TEXT)
- cover_image_id (TEXT)
- privacy_setting (TEXT DEFAULT 'private')
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- image_count (INTEGER DEFAULT 0)

Album_Images table:
- album_id (TEXT)
- image_id (TEXT)
- added_at (TIMESTAMP)
- display_order (INTEGER)

Image_Metadata table:
- image_id (TEXT PRIMARY KEY)
- exif_data (TEXT) -- JSON
- camera_make (TEXT)
- camera_model (TEXT)
- date_taken (TIMESTAMP)
- location_lat (DECIMAL)
- location_lon (DECIMAL)
- focal_length (DECIMAL)
- aperture (TEXT)
- iso (INTEGER)
- shutter_speed (TEXT)

Tags table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- usage_count (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)

Image_Tags table:
- image_id (TEXT)
- tag_id (INTEGER)
- added_at (TIMESTAMP)
```

## Image Processing Features

- **Automatic thumbnail generation** in multiple sizes
- **Image optimization** for web display
- **EXIF metadata extraction** and storage
- **Image format conversion** (JPEG, PNG, WebP)
- **Watermark application** for protection
- **Image resizing** and cropping
- **Color profile management**
- **Duplicate detection** using hashing

## Gallery Organization Features

- **Album creation** and management
- **Hierarchical album** structure support
- **Image tagging** with autocomplete
- **Bulk operations** for multiple images
- **Drag-and-drop** album organization
- **Privacy controls** (public, private, shared)
- **Cover image** selection for albums
- **Sorting and filtering** options

## Security and Validation Features

- **File type validation** using magic numbers
- **File size limits** and validation
- **Image dimension** validation
- **Malicious file detection**
- **User quota** enforcement
- **Access control** for private galleries
- **Secure file storage** with unique names
- **Rate limiting** for uploads

## Performance Optimization Features

- **Lazy loading** for large galleries
- **Progressive image** loading
- **CDN integration** support
- **Caching strategies** for thumbnails
- **Database indexing** for fast queries
- **Image compression** optimization
- **Batch processing** capabilities

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, Pillow, python-magic, etc.

3. **Production Ready Features**
   - Comprehensive error handling
   - Image validation and security
   - File storage management
   - Metadata extraction and processing
   - Performance optimization for large galleries
   - Batch operation support
   - Access logging and monitoring
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all gallery scenarios including image upload, processing, organization, metadata management, and security with proper validation and performance optimization.