# Backend Generation Prompt - Flask Wiki Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/pages`, `/api/search`, `/api/history`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Wiki System Backend**  
A comprehensive Flask backend for wiki platform, featuring page management, content organization, version control, search functionality, collaborative editing, and knowledge base management with markdown support.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete page creation, editing, and management system
- Hierarchical content organization with categories and namespaces
- Full-text search functionality across all content
- Comprehensive version history and revision control
- Markdown formatting with live preview support
- User authentication and collaborative editing
- Page linking and reference management
- Access control and permission management
- File attachments and media handling
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
import markdown
import bleach
from difflib import unified_diff
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Content Processing (Markdown)
# 5. Version Control Logic
# 6. Search Indexing
# 7. API Routes:
#    - GET /api/pages (list pages)
#    - GET /api/pages/<slug> (get page content)
#    - POST /api/pages (create page)
#    - PUT /api/pages/<slug> (update page)
#    - DELETE /api/pages/<slug> (delete page)
#    - GET /api/pages/<slug>/history (get page history)
#    - GET /api/pages/<slug>/revisions/<id> (get specific revision)
#    - POST /api/pages/<slug>/revert (revert to revision)
#    - GET /api/search (search pages)
#    - GET /api/categories (get categories)
#    - POST /api/categories (create category)
#    - GET /api/pages/<slug>/links (get page links)
#    - GET /api/pages/<slug>/backlinks (get backlinks)
#    - POST /api/pages/<slug>/attachments (upload attachment)
#    - GET /api/attachments/<id> (download attachment)
#    - GET /api/recent (get recent changes)
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
   - Accept: username, email, password, full_name
   - Validate input and create user account
   - Set default user permissions
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and permissions

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include user permissions and contribution stats

### Page Management Routes

5. **GET /api/pages**
   - Return list of wiki pages
   - Support filtering by category, namespace, author
   - Include page metadata and summaries
   - Support pagination and sorting

6. **GET /api/pages/<slug>**
   - Return specific page content
   - Include rendered HTML and raw markdown
   - Show page metadata and edit permissions
   - Track page views and analytics

7. **POST /api/pages**
   - Create new wiki page
   - Accept: title, content, category, tags, summary
   - Generate unique slug from title
   - Process markdown and create initial revision
   - Return created page

8. **PUT /api/pages/<slug>**
   - Update existing page
   - Accept: content, summary, tags, category
   - Create new revision with diff
   - Process markdown and update links
   - Return updated page

9. **DELETE /api/pages/<slug>**
   - Delete wiki page
   - Handle page dependencies and links
   - Archive content for potential recovery
   - Return confirmation

### Version Control Routes

10. **GET /api/pages/<slug>/history**
    - Return page revision history
    - Include revision metadata and summaries
    - Show diff statistics and contributors
    - Support pagination for long histories

11. **GET /api/pages/<slug>/revisions/<id>**
    - Return specific page revision
    - Include content at that point in time
    - Show revision details and changes
    - Support diff comparison

12. **POST /api/pages/<slug>/revert**
    - Revert page to specific revision
    - Accept: revision_id, revert_summary
    - Create new revision with reverted content
    - Update page links and references

### Search and Discovery Routes

13. **GET /api/search**
    - Search across all wiki content
    - Accept: query, filters (category, author, date)
    - Support advanced search operators
    - Return ranked results with highlights

14. **GET /api/categories**
    - Return list of page categories
    - Include page counts and descriptions
    - Support hierarchical categories

15. **POST /api/categories**
    - Create new category
    - Accept: name, description, parent_category
    - Validate category hierarchy
    - Return created category

### Page Relationship Routes

16. **GET /api/pages/<slug>/links**
    - Return outbound links from page
    - Include internal and external links
    - Show link status and validation

17. **GET /api/pages/<slug>/backlinks**
    - Return pages that link to this page
    - Include link context and relevance
    - Support relationship analysis

18. **POST /api/pages/<slug>/attachments**
    - Upload file attachment to page
    - Accept: file, description, access_level
    - Validate file type and size
    - Return attachment info

19. **GET /api/attachments/<id>**
    - Download page attachment
    - Validate user permissions
    - Track download statistics

20. **GET /api/recent**
    - Return recent changes across wiki
    - Include page edits, new pages, deletions
    - Support filtering by user and timeframe
    - Show change summaries and diffs

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- full_name (TEXT)
- created_at (TIMESTAMP)
- last_active (TIMESTAMP)
- edit_count (INTEGER DEFAULT 0)
- is_admin (BOOLEAN DEFAULT FALSE)

Pages table:
- id (TEXT PRIMARY KEY)
- slug (TEXT UNIQUE NOT NULL)
- title (TEXT NOT NULL)
- content (TEXT)
- html_content (TEXT)
- category_id (INTEGER)
- created_by (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- view_count (INTEGER DEFAULT 0)
- is_protected (BOOLEAN DEFAULT FALSE)
- namespace (TEXT DEFAULT 'main')

Page_Revisions table:
- id (TEXT PRIMARY KEY)
- page_id (TEXT)
- content (TEXT NOT NULL)
- summary (TEXT)
- editor_id (TEXT)
- created_at (TIMESTAMP)
- content_length (INTEGER)
- changes_count (INTEGER)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- parent_id (INTEGER)
- page_count (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)

Page_Links table:
- id (TEXT PRIMARY KEY)
- source_page_id (TEXT)
- target_page_slug (TEXT)
- link_text (TEXT)
- is_external (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)

Tags table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- usage_count (INTEGER DEFAULT 0)

Page_Tags table:
- page_id (TEXT)
- tag_id (INTEGER)
- added_at (TIMESTAMP)

Attachments table:
- id (TEXT PRIMARY KEY)
- page_id (TEXT)
- filename (TEXT NOT NULL)
- original_filename (TEXT)
- file_size (INTEGER)
- mime_type (TEXT)
- uploaded_by (TEXT)
- uploaded_at (TIMESTAMP)
- download_count (INTEGER DEFAULT 0)

Search_Index table:
- page_id (TEXT PRIMARY KEY)
- title_tokens (TEXT)
- content_tokens (TEXT)
- updated_at (TIMESTAMP)
```

## Wiki Content Features

- **Markdown processing** with extended syntax support
- **Content sanitization** to prevent XSS attacks
- **Automatic link detection** and page references
- **Table of contents** generation from headers
- **Code syntax highlighting** for technical documentation
- **Mathematical notation** support with LaTeX
- **Embedded media** support (images, videos)
- **Template system** for reusable content blocks

## Version Control Features

- **Complete revision history** with diff visualization
- **Content comparison** between any two revisions
- **Revert functionality** with conflict resolution
- **Edit summaries** and change documentation
- **Collaborative editing** with merge conflict handling
- **Protected pages** with admin-only editing
- **Draft system** for work-in-progress content
- **Change notifications** and watchlist functionality

## Search and Navigation Features

- **Full-text search** with ranking and relevance
- **Advanced search** with filters and operators
- **Category browsing** with hierarchical organization
- **Tag-based discovery** and content clustering
- **Related pages** suggestions based on content
- **Recently viewed** and popular pages tracking
- **Random page** discovery for exploration
- **Sitemap generation** for SEO and navigation

## Access Control and Security Features

- **Role-based permissions** (admin, editor, viewer)
- **Page-level protection** and access control
- **Edit restrictions** based on user experience
- **Vandalism detection** and automatic rollback
- **Content moderation** and approval workflows
- **User contribution** tracking and statistics
- **Spam prevention** and rate limiting
- **Audit logging** for administrative actions

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, markdown, bleach, text processing libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Content validation and sanitization
   - Version control with conflict resolution
   - Search indexing and optimization
   - Access control and security measures
   - Performance optimization for large wikis
   - Backup and export capabilities
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all wiki scenarios including content management, version control, collaborative editing, search functionality, and access control with proper validation and security measures.