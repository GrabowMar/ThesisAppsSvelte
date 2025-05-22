# Backend Generation Prompt - Flask Feedback Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/feedback`, `/api/submissions`, `/api/analytics`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Feedback System Backend**  
A comprehensive Flask backend for feedback collection application, featuring form submission handling, data storage, validation, and response management capabilities.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Multi-field feedback form processing
- Server-side form validation
- Submission handling and storage
- Response storage and retrieval
- Success/error response management
- Data analytics endpoints
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
import re
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Validation Logic
# 5. Utility Functions
# 6. API Routes:
#    - POST /api/feedback (submit feedback)
#    - GET /api/feedback (get all feedback - admin)
#    - GET /api/feedback/<id> (get specific feedback)
#    - GET /api/analytics (get feedback statistics)
#    - GET /api/categories (get feedback categories)
#    - POST /api/categories (create new category)
#    - DELETE /api/feedback/<id> (delete feedback - admin)
# 7. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

1. **POST /api/feedback**
   - Accept: name, email, category, subject, message, rating
   - Validate all input fields
   - Store feedback in database
   - Return success/error response with submission ID

2. **GET /api/feedback**
   - Return paginated list of all feedback submissions
   - Include filtering options (category, rating, date)
   - Admin/protected route functionality

3. **GET /api/feedback/<id>**
   - Return specific feedback submission by ID
   - Include submission details and metadata

4. **GET /api/analytics**
   - Return feedback statistics and metrics
   - Include category breakdown, rating averages, submission trends

5. **GET /api/categories**
   - Return list of available feedback categories
   - Include category descriptions and usage counts

6. **POST /api/categories**
   - Create new feedback category
   - Accept: name, description
   - Return created category info

7. **DELETE /api/feedback/<id>**
   - Delete specific feedback submission
   - Admin functionality with proper authorization

## Validation Requirements

- **Name:** Required, 2-50 characters, alphabetic with spaces
- **Email:** Required, valid email format
- **Category:** Required, must exist in predefined categories
- **Subject:** Required, 5-100 characters
- **Message:** Required, 10-1000 characters
- **Rating:** Optional, integer between 1-5
- **Server-side sanitization** of all inputs
- **Rate limiting** for submission prevention

## Database Schema

```sql
Feedback table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- email (TEXT NOT NULL)
- category (TEXT NOT NULL)
- subject (TEXT NOT NULL)
- message (TEXT NOT NULL)
- rating (INTEGER)
- submitted_at (TIMESTAMP)
- ip_address (TEXT)
- user_agent (TEXT)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- created_at (TIMESTAMP)

Analytics table:
- id (INTEGER PRIMARY KEY)
- submission_date (DATE)
- category (TEXT)
- rating (INTEGER)
- response_time (INTEGER)
```

## Security Features

- Input validation and sanitization
- SQL injection prevention
- Rate limiting for submissions
- Email format validation
- XSS protection
- CSRF protection considerations
- IP address logging for abuse prevention

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, email-validator, etc.

3. **Production Ready Features**
   - Comprehensive input validation
   - Error handling with proper HTTP status codes
   - Rate limiting implementation
   - Database connection management
   - Logging for debugging and monitoring
   - JSON responses with consistent format
   - Email notification capabilities (optional)

**Very important:** Your backend should be feature rich, production ready, and handle all feedback submission scenarios including validation errors, duplicate submissions, and data integrity concerns.