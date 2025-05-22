# Backend Generation Prompt - Flask Notes Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/notes`, `/api/categories`, `/api/search`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Notes System Backend**  
A comprehensive Flask backend for notes application, featuring note management, categorization, search functionality, and archiving capabilities with robust content handling.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Note creation, editing, and deletion
- Note listing and viewing with pagination
- Category management and organization
- Full-text search functionality
- Note archiving and restoration
- Auto-save functionality
- Note tagging system
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import uuid
import re

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Search Logic
# 5. Content Processing
# 6. Utility Functions
# 7. API Routes:
#    - GET /api/notes (get all notes with pagination/filtering)
#    - GET /api/notes/<id> (get specific note)
#    - POST /api/notes (create new note)
#    - PUT /api/notes/<id> (update note)
#    - DELETE /api/notes/<id> (delete note)
#    - POST /api/notes/<id>/archive (archive note)
#    - POST /api/notes/<id>/restore (restore archived note)
#    - GET /api/categories (get all categories)
#    - POST /api/categories (create category)
#    - PUT /api/categories/<id> (update category)
#    - DELETE /api/categories/<id> (delete category)
#    - GET /api/search (search notes)
#    - GET /api/tags (get all tags)
#    - POST /api/notes/<id>/auto-save (auto-save functionality)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Note Management Routes

1. **GET /api/notes**
   - Return paginated list of notes
   - Support filtering by category, archived status, date range
   - Include note previews, metadata, and timestamps
   - Support sorting by date, title, category

2. **GET /api/notes/<id>**
   - Return specific note with full content
   - Include all metadata, tags, and category info
   - Track last accessed time

3. **POST /api/notes**
   - Create new note
   - Accept: title, content, category_id, tags
   - Validate input and generate unique ID
   - Return created note with metadata

4. **PUT /api/notes/<id>**
   - Update existing note
   - Accept: title, content, category_id, tags
   - Update timestamp and version tracking
   - Return updated note

5. **DELETE /api/notes/<id>**
   - Delete note (soft delete or permanent)
   - Option for moving to trash vs permanent deletion
   - Return confirmation response

6. **POST /api/notes/<id>/archive**
   - Archive specific note
   - Update archived status and timestamp
   - Return success response

7. **POST /api/notes/<id>/restore**
   - Restore archived note
   - Update archived status
   - Return restored note

8. **POST /api/notes/<id>/auto-save**
   - Auto-save note content during editing
   - Accept: content, title
   - Update without changing main timestamp
   - Return save confirmation

### Category Management Routes

9. **GET /api/categories**
   - Return list of all categories
   - Include note counts for each category
   - Support hierarchical categories

10. **POST /api/categories**
    - Create new category
    - Accept: name, description, color
    - Validate uniqueness
    - Return created category

11. **PUT /api/categories/<id>**
    - Update category details
    - Accept: name, description, color
    - Return updated category

12. **DELETE /api/categories/<id>**
    - Delete category
    - Handle notes in deleted category (reassign or uncategorize)
    - Return confirmation

### Search and Tags Routes

13. **GET /api/search**
    - Full-text search across notes
    - Accept: query, category_filter, date_range
    - Search in title, content, and tags
    - Return ranked search results

14. **GET /api/tags**
    - Return list of all tags used in notes
    - Include usage counts
    - Support tag autocomplete

## Database Schema

```sql
Notes table:
- id (TEXT PRIMARY KEY)
- title (TEXT NOT NULL)
- content (TEXT)
- category_id (INTEGER)
- is_archived (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- last_accessed (TIMESTAMP)
- auto_save_content (TEXT)
- auto_save_timestamp (TIMESTAMP)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- color (TEXT)
- created_at (TIMESTAMP)

Tags table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- created_at (TIMESTAMP)

Note_Tags table:
- note_id (TEXT)
- tag_id (INTEGER)
- created_at (TIMESTAMP)

Search_Index table:
- note_id (TEXT)
- content_tokens (TEXT)
- updated_at (TIMESTAMP)
```

## Search and Content Features

- **Full-text search** with ranking and relevance scoring
- **Auto-complete** for tags and categories
- **Content indexing** for fast search operations
- **Tag extraction** from note content
- **Related notes** suggestions based on content similarity
- **Search history** and saved searches
- **Advanced search** with filters and operators

## Utility Features

- **Auto-save** with configurable intervals
- **Version tracking** for note changes
- **Content validation** and sanitization
- **Export functionality** (JSON, plain text)
- **Import functionality** from various formats
- **Backup and restore** capabilities
- **Note statistics** and analytics

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, text processing libraries, etc.

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation and sanitization
   - Full-text search implementation
   - Auto-save functionality
   - Database transaction management
   - Content indexing and search optimization
   - Proper HTTP status codes
   - JSON responses with consistent format
   - Performance optimization for large note collections

**Very important:** Your backend should be feature rich, production ready, and handle all note-taking scenarios including content management, search functionality, categorization, archiving, and auto-save with proper validation and performance optimization.