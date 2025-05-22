# Backend Generation Prompt - Flask Microblog Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/posts`, `/api/users`, `/api/feed`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Microblog System Backend**  
A comprehensive Flask backend for microblog application, featuring post management, user profiles, social interactions, timeline feeds, and search capabilities with real-time engagement features.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete CRUD operations for posts
- User authentication and profile management
- Timeline/feed generation with personalized content
- Post interactions (likes, comments, shares)
- Follow/unfollow user functionality
- Real-time post search and discovery
- User activity tracking and analytics
- Content moderation capabilities
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
import hashlib
import re

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Authentication Logic
# 5. Feed Generation Logic
# 6. Interaction Handling
# 7. API Routes:
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - GET /api/posts (get posts with pagination/filtering)
#    - GET /api/posts/<id> (get specific post)
#    - POST /api/posts (create new post)
#    - PUT /api/posts/<id> (update post)
#    - DELETE /api/posts/<id> (delete post)
#    - GET /api/feed (get personalized feed)
#    - GET /api/users/<id> (get user profile)
#    - PUT /api/users/<id> (update user profile)
#    - GET /api/users/<id>/posts (get user's posts)
#    - POST /api/users/<id>/follow (follow user)
#    - DELETE /api/users/<id>/follow (unfollow user)
#    - GET /api/users/<id>/followers (get followers)
#    - GET /api/users/<id>/following (get following)
#    - POST /api/posts/<id>/like (like/unlike post)
#    - GET /api/posts/<id>/likes (get post likes)
#    - POST /api/posts/<id>/comments (add comment)
#    - GET /api/posts/<id>/comments (get comments)
#    - PUT /api/comments/<id> (update comment)
#    - DELETE /api/comments/<id> (delete comment)
#    - GET /api/search (search posts and users)
#    - GET /api/trending (get trending posts/hashtags)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, display_name
   - Validate input and create user account
   - Hash password securely
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and authentication status

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include profile stats (posts, followers, following)

### Post Management Routes

5. **GET /api/posts**
   - Return paginated list of posts
   - Support filtering by user, date range, hashtags
   - Support sorting by date, popularity, engagement
   - Include post metadata and interaction counts

6. **GET /api/posts/<id>**
   - Return specific post with full details
   - Include author info, interaction counts, comments
   - Track post views

7. **POST /api/posts**
   - Create new post
   - Accept: content, media_urls, hashtags
   - Require authentication
   - Process hashtags and mentions
   - Return created post

8. **PUT /api/posts/<id>**
   - Update existing post
   - Require authentication and ownership
   - Track edit history
   - Return updated post

9. **DELETE /api/posts/<id>**
   - Delete post
   - Require authentication and ownership
   - Handle related interactions cleanup
   - Return confirmation

### Feed and Timeline Routes

10. **GET /api/feed**
    - Return personalized user feed
    - Include posts from followed users
    - Algorithm-based content curation
    - Support infinite scroll pagination

### User Profile Routes

11. **GET /api/users/<id>**
    - Return user profile information
    - Include bio, stats, recent activity
    - Public profile data only

12. **PUT /api/users/<id>**
    - Update user profile
    - Accept: display_name, bio, avatar_url, location
    - Require authentication and ownership
    - Return updated profile

13. **GET /api/users/<id>/posts**
    - Return user's posts with pagination
    - Support filtering by post type
    - Include interaction counts

### Social Interaction Routes

14. **POST /api/users/<id>/follow**
    - Follow/unfollow user
    - Require authentication
    - Update follower/following counts
    - Return relationship status

15. **DELETE /api/users/<id>/follow**
    - Unfollow user
    - Require authentication
    - Update counts
    - Return confirmation

16. **GET /api/users/<id>/followers**
    - Return user's followers list
    - Support pagination
    - Include follower profiles

17. **GET /api/users/<id>/following**
    - Return list of users being followed
    - Support pagination
    - Include user profiles

### Post Interaction Routes

18. **POST /api/posts/<id>/like**
    - Like/unlike post
    - Require authentication
    - Toggle like status
    - Update like count

19. **GET /api/posts/<id>/likes**
    - Return list of users who liked post
    - Support pagination
    - Include user profiles

20. **POST /api/posts/<id>/comments**
    - Add comment to post
    - Accept: content
    - Require authentication
    - Return created comment

21. **GET /api/posts/<id>/comments**
    - Return post comments
    - Support pagination and threading
    - Include comment metadata

22. **PUT /api/comments/<id>**
    - Update comment
    - Require authentication and ownership
    - Return updated comment

23. **DELETE /api/comments/<id>**
    - Delete comment
    - Require authentication and ownership
    - Return confirmation

### Search and Discovery Routes

24. **GET /api/search**
    - Search posts and users
    - Accept: query, type (posts/users/hashtags)
    - Support advanced search operators
    - Return ranked results

25. **GET /api/trending**
    - Return trending posts and hashtags
    - Time-based trending calculation
    - Support different time ranges

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- display_name (TEXT)
- bio (TEXT)
- avatar_url (TEXT)
- location (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- post_count (INTEGER DEFAULT 0)
- follower_count (INTEGER DEFAULT 0)
- following_count (INTEGER DEFAULT 0)
- is_verified (BOOLEAN DEFAULT FALSE)

Posts table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- content (TEXT NOT NULL)
- media_urls (TEXT) -- JSON array
- hashtags (TEXT) -- JSON array
- mentions (TEXT) -- JSON array
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- like_count (INTEGER DEFAULT 0)
- comment_count (INTEGER DEFAULT 0)
- share_count (INTEGER DEFAULT 0)
- view_count (INTEGER DEFAULT 0)

Comments table:
- id (TEXT PRIMARY KEY)
- post_id (TEXT)
- user_id (TEXT)
- content (TEXT NOT NULL)
- parent_id (TEXT) -- for reply threading
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- like_count (INTEGER DEFAULT 0)

Likes table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- target_id (TEXT) -- post or comment ID
- target_type (TEXT) -- 'post' or 'comment'
- created_at (TIMESTAMP)

Follows table:
- id (TEXT PRIMARY KEY)
- follower_id (TEXT)
- following_id (TEXT)
- created_at (TIMESTAMP)

Hashtags table:
- id (INTEGER PRIMARY KEY)
- tag (TEXT UNIQUE NOT NULL)
- usage_count (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)

Post_Views table:
- post_id (TEXT)
- user_id (TEXT)
- viewed_at (TIMESTAMP)
```

## Social Media Features

- **Hashtag processing** with trending calculation
- **Mention system** with notifications
- **Media handling** for images and videos
- **Real-time engagement** tracking
- **Content recommendation** algorithm
- **User discovery** and suggestions
- **Activity feeds** and notifications
- **Content moderation** tools

## Feed Algorithm Features

- **Chronological timeline** for recent posts
- **Engagement-based ranking** for popular content
- **Personalized recommendations** based on interactions
- **Diversity injection** to show varied content
- **Following-based prioritization**
- **Hashtag and interest-based suggestions**

## Security and Validation Features

- User authentication and session management
- Input validation and content sanitization
- Rate limiting for posts and interactions
- Spam detection and prevention
- Content moderation capabilities
- Privacy controls for user profiles
- Abuse reporting system

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, text processing, media handling libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation and sanitization
   - Authentication and authorization
   - Social interaction management
   - Feed generation optimization
   - Content moderation tools
   - Performance optimization for social features
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all microblog scenarios including post management, social interactions, feed generation, and user engagement with proper validation and performance optimization.