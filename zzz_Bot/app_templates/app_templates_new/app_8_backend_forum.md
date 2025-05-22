# Backend Generation Prompt - Flask Forum Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/threads`, `/api/comments`, `/api/categories`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Forum System Backend**  
A comprehensive Flask backend for forum application, featuring thread management, comment system, categorization, search functionality, and user interaction capabilities.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Thread creation, viewing, editing, and deletion
- Nested comment system with replies
- Category management and organization
- Thread and comment sorting capabilities
- Search functionality across threads and comments
- User management and authentication
- Vote/rating system for threads and comments
- Moderation capabilities
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
import hashlib
import re

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Authentication Logic
# 5. Search and Sorting Logic
# 6. Utility Functions
# 7. API Routes:
#    - GET /api/threads (list threads with pagination/filtering)
#    - GET /api/threads/<id> (get thread details)
#    - POST /api/threads (create new thread)
#    - PUT /api/threads/<id> (update thread)
#    - DELETE /api/threads/<id> (delete thread)
#    - GET /api/threads/<id>/comments (get thread comments)
#    - POST /api/threads/<id>/comments (add comment to thread)
#    - PUT /api/comments/<id> (update comment)
#    - DELETE /api/comments/<id> (delete comment)
#    - POST /api/comments/<id>/reply (reply to comment)
#    - GET /api/categories (get all categories)
#    - POST /api/categories (create category)
#    - PUT /api/categories/<id> (update category)
#    - DELETE /api/categories/<id> (delete category)
#    - GET /api/search (search threads and comments)
#    - POST /api/threads/<id>/vote (vote on thread)
#    - POST /api/comments/<id>/vote (vote on comment)
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
   - Protected route

### Thread Management Routes

5. **GET /api/threads**
   - Return paginated list of threads
   - Support filtering by category, author, date
   - Support sorting by date, votes, comments, activity
   - Include thread metadata and preview

6. **GET /api/threads/<id>**
   - Return specific thread with full content
   - Include author info, vote counts, view counts
   - Track thread views

7. **POST /api/threads**
   - Create new thread
   - Accept: title, content, category_id
   - Require authentication
   - Return created thread

8. **PUT /api/threads/<id>**
   - Update existing thread
   - Require authentication and ownership
   - Accept: title, content, category_id
   - Track edit history

9. **DELETE /api/threads/<id>**
   - Delete thread
   - Require authentication and ownership/admin
   - Soft delete with recovery option

### Comment System Routes

10. **GET /api/threads/<id>/comments**
    - Return comments for specific thread
    - Support nested/threaded comments
    - Include vote counts and author info
    - Support pagination for large comment threads

11. **POST /api/threads/<id>/comments**
    - Add comment to thread
    - Accept: content, parent_id (for replies)
    - Require authentication
    - Return created comment

12. **PUT /api/comments/<id>**
    - Update comment
    - Require authentication and ownership
    - Track edit history

13. **DELETE /api/comments/<id>**
    - Delete comment
    - Require authentication and ownership/admin
    - Handle nested comment deletion

14. **POST /api/comments/<id>/reply**
    - Reply to specific comment
    - Accept: content
    - Create nested comment structure
    - Require authentication

### Category Management Routes

15. **GET /api/categories**
    - Return list of forum categories
    - Include thread counts and descriptions
    - Support hierarchical categories

16. **POST /api/categories**
    - Create new category
    - Accept: name, description, parent_id
    - Require admin authentication

17. **PUT /api/categories/<id>**
    - Update category details
    - Require admin authentication

18. **DELETE /api/categories/<id>**
    - Delete category
    - Handle threads in deleted category
    - Require admin authentication

### Search and Voting Routes

19. **GET /api/search**
    - Search threads and comments
    - Accept: query, category_filter, sort_by
    - Support advanced search operators
    - Return ranked results

20. **POST /api/threads/<id>/vote**
    - Vote on thread (upvote/downvote)
    - Accept: vote_type
    - Require authentication
    - Prevent duplicate voting

21. **POST /api/comments/<id>/vote**
    - Vote on comment
    - Accept: vote_type
    - Require authentication
    - Update comment score

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- created_at (TIMESTAMP)
- is_admin (BOOLEAN DEFAULT FALSE)
- post_count (INTEGER DEFAULT 0)
- reputation (INTEGER DEFAULT 0)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- parent_id (INTEGER)
- thread_count (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)

Threads table:
- id (TEXT PRIMARY KEY)
- title (TEXT NOT NULL)
- content (TEXT NOT NULL)
- author_id (TEXT)
- category_id (INTEGER)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- view_count (INTEGER DEFAULT 0)
- vote_score (INTEGER DEFAULT 0)
- comment_count (INTEGER DEFAULT 0)
- is_pinned (BOOLEAN DEFAULT FALSE)
- is_locked (BOOLEAN DEFAULT FALSE)

Comments table:
- id (TEXT PRIMARY KEY)
- thread_id (TEXT)
- author_id (TEXT)
- content (TEXT NOT NULL)
- parent_id (TEXT) -- for nested comments
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- vote_score (INTEGER DEFAULT 0)
- depth_level (INTEGER DEFAULT 0)

Votes table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- target_id (TEXT) -- thread or comment ID
- target_type (TEXT) -- 'thread' or 'comment'
- vote_type (TEXT) -- 'up' or 'down'
- created_at (TIMESTAMP)

Thread_Views table:
- thread_id (TEXT)
- user_id (TEXT)
- viewed_at (TIMESTAMP)
```

## Forum Features

- **Threaded discussions** with proper nesting
- **Vote system** for content quality ranking
- **Category organization** with hierarchical structure
- **Search functionality** with full-text indexing
- **User reputation** system based on contributions
- **Moderation tools** for content management
- **Thread pinning** and locking capabilities
- **View tracking** and activity monitoring

## Security and Validation Features

- User authentication and session management
- Input validation and sanitization
- SQL injection prevention
- XSS protection for user content
- Rate limiting for posting and voting
- Spam detection and prevention
- Content moderation capabilities
- User permission system

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, text processing libraries, etc.

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation and sanitization
   - Authentication and authorization
   - Search optimization with indexing
   - Vote system with duplicate prevention
   - Content moderation tools
   - Performance optimization for large discussions
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all forum scenarios including thread management, comment systems, user authentication, search functionality, and voting with proper validation and moderation capabilities.