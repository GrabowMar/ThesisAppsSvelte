# Backend Generation Prompt - Flask Login/Register Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper security.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/login`, `/api/register`, `/api/dashboard`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Authentication System Backend**  
A secure Flask backend for user authentication system, featuring user registration and login capabilities with core security features.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- User registration endpoint
- Login functionality endpoint
- Password security (hashing)
- Session management
- Error handling and validation
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import hashlib
import sqlite3
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Authentication Logic
# 5. Utility Functions
# 6. API Routes:
#    - POST /api/register
#    - POST /api/login
#    - POST /api/logout
#    - GET /api/user (get current user)
#    - GET /api/dashboard (protected route)
# 7. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

1. **POST /api/register**
   - Accept: username, email, password
   - Validate input
   - Hash password
   - Store user in database
   - Return success/error response

2. **POST /api/login**
   - Accept: username/email, password
   - Validate credentials
   - Create session
   - Return success/error response

3. **POST /api/logout**
   - Clear session
   - Return success response

4. **GET /api/user**
   - Return current user info if logged in
   - Protected route

5. **GET /api/dashboard**
   - Protected dashboard data
   - Require authentication

## Security Requirements

- Password hashing (bcrypt or similar)
- Input validation and sanitization
- SQL injection prevention
- Session management
- Error handling without information leakage
- CORS configuration

## Database Schema

```sql
Users table:
- id (INTEGER PRIMARY KEY)
- username (TEXT UNIQUE)
- email (TEXT UNIQUE) 
- password_hash (TEXT)
- created_at (TIMESTAMP)
```

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation
   - Security best practices
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all authentication scenarios including edge cases and error conditions.