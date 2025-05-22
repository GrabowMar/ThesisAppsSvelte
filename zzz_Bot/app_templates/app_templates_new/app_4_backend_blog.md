# Backend Generation Prompt - Flask Blog Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper authentication.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/auth`, `/api/posts`, `/api/comments`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Blog System Backend**  
A comprehensive Flask backend for blog application, featuring user authentication, content management, comment system, and post categorization with markdown support.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- User authentication (login/register) with session management
- Blog post creation, editing, and deletion
- Comment system with nested replies
- Post categorization and tagging
- Markdown content processing
- User management and profiles
- Search functionality
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
import hashlib
import markdown
import bleach
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Authentication Logic
# 5. Content Processing (Markdown)
# 6. Utility Functions
# 7. API Routes:
#    - POST /api/auth/register
#    - POST /api/auth/login
#    - POST /api/auth/logout
#    - GET /api/auth/user
#    - GET /api/posts (with pagination, filtering)
#    - GET /api/posts/<id>
#    - POST /api/posts
#    - PUT /api/posts/<id>
#    - DELETE /api/posts/<id>
#    - GET /api/posts/<id>/comments
#    - POST /api/posts/<id>/comments
#    - PUT /api/comments/<id>
#    - DELETE /api/comments/<id>
#    - GET /api/categories
#    - POST /api/categories
#    - GET /api/search
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password
   - Validate input and hash password
   - Create user account
   - Return success/error response

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create session
   - Return user info and session

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Protected route

### Blog Post Routes

5. **GET /api/posts**
   - Return paginated list of blog posts
   - Support filtering by category, author, date
   - Include post metadata and excerpts

6. **GET /api/posts/<id>**
   - Return specific blog post with full content
   - Include author info and metadata
   - Convert markdown to HTML

7. **POST /api/posts**
   - Create new blog post
   - Accept: title, content, category, tags
   - Require authentication
   - Process markdown content

8. **PUT /api/posts/<id>**
   - Update existing blog post
   - Require authentication and ownership
   - Version control support

9. **DELETE /api/posts/<id>**
   - Delete blog post
   - Require authentication and ownership
   - Soft delete with archive

### Comment Routes

10. **GET /api/posts/<id>/comments**
    - Return comments for specific post
    - Support nested/threaded comments
    - Include author info

11. **POST /api/posts/<id>/comments**
    - Add comment to blog post
    - Accept: content, parent_id (for replies)
    - Require authentication

12. **PUT /api/comments/<id>**
    - Update comment
    - Require authentication and ownership

13. **DELETE /api/comments/<id>**
    - Delete comment
    - Require authentication and ownership

### Category and Search Routes

14. **GET /api/categories**
    - Return list of blog categories
    - Include post counts

15. **POST /api/categories**
    - Create new category
    - Require admin authentication

16. **GET /api/search**
    - Search blog posts by title, content, tags
    - Return paginated results

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- created_at (TIMESTAMP)
- is_admin (BOOLEAN DEFAULT FALSE)

Posts table:
- id (TEXT PRIMARY KEY)
- title (TEXT NOT NULL)
- content (TEXT NOT NULL)
- html_content (TEXT)
- excerpt (TEXT)
- author_id (TEXT)
- category_id (INTEGER)
- published (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- created_at (TIMESTAMP)

Comments table:
- id (TEXT PRIMARY KEY)
- post_id (TEXT)
- author_id (TEXT)
- content (TEXT NOT NULL)
- parent_id (TEXT) -- for nested comments
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Tags table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)

Post_Tags table:
- post_id (TEXT)
- tag_id (INTEGER)
```

## Content Processing Features

- **Markdown to HTML conversion** with safe rendering
- **Content sanitization** to prevent XSS attacks
- **Auto-excerpt generation** from post content
- **Tag extraction** from content
- **Image handling** and optimization
- **Code syntax highlighting** support

## Security Features

- Password hashing with salt
- Session management
- Input validation and sanitization
- SQL injection prevention
- XSS protection with content sanitization
- Authentication required for protected routes
- User ownership verification for edit/delete operations

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, markdown, bleach, etc.

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation and sanitization
   - Authentication and authorization
   - Content processing and security
   - Database transaction management
   - Logging and monitoring
   - API rate limiting
   - Proper HTTP status codes

**Very important:** Your backend should be feature rich, production ready, and handle all blog functionality including user management, content creation/editing, comment system, and secure authentication with proper content processing.