# Backend Generation Prompt - Flask Polling Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/polls`, `/api/votes`, `/api/analytics`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Polling System Backend**  
A comprehensive Flask backend for polling application, featuring poll creation, vote management, real-time results, analytics dashboard, and time-based poll controls with security and fraud prevention.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete poll creation and management system
- Secure vote casting with duplicate prevention
- Real-time results calculation and display
- Advanced analytics and reporting
- Time-limited polls with automatic closure
- Multiple poll types (single choice, multiple choice, ranking)
- User authentication and poll ownership
- Vote verification and audit trails
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
import json
from collections import Counter

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Vote Validation Logic
# 5. Analytics Calculation
# 6. Time Management
# 7. API Routes:
#    - GET /api/polls (list polls with pagination/filtering)
#    - GET /api/polls/<id> (get specific poll)
#    - POST /api/polls (create new poll)
#    - PUT /api/polls/<id> (update poll)
#    - DELETE /api/polls/<id> (delete poll)
#    - POST /api/polls/<id>/vote (cast vote)
#    - GET /api/polls/<id>/results (get poll results)
#    - GET /api/polls/<id>/analytics (get detailed analytics)
#    - GET /api/polls/<id>/voters (get voter list - admin)
#    - POST /api/polls/<id>/close (manually close poll)
#    - GET /api/polls/my (get user's polls)
#    - GET /api/polls/active (get active polls)
#    - GET /api/polls/recent (get recent polls)
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - GET /api/analytics/summary (global analytics)
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
   - Include user stats (polls created, votes cast)

### Poll Management Routes

5. **GET /api/polls**
   - Return paginated list of polls
   - Support filtering by status, category, creator
   - Support sorting by date, popularity, votes
   - Include poll metadata and status

6. **GET /api/polls/<id>**
   - Return specific poll with full details
   - Include options, vote counts, and metadata
   - Check if user has already voted
   - Respect poll privacy settings

7. **POST /api/polls**
   - Create new poll
   - Accept: title, description, options, poll_type, end_date, settings
   - Validate poll structure and timing
   - Return created poll with unique ID

8. **PUT /api/polls/<id>**
   - Update existing poll
   - Require authentication and ownership
   - Restrict updates based on poll status
   - Return updated poll

9. **DELETE /api/polls/<id>**
   - Delete poll
   - Require authentication and ownership
   - Handle votes cleanup
   - Return confirmation

10. **POST /api/polls/<id>/close**
    - Manually close poll before end time
    - Require authentication and ownership
    - Update poll status and calculate final results

### Voting Routes

11. **POST /api/polls/<id>/vote**
    - Cast vote on poll
    - Accept: option_ids (single or multiple based on poll type)
    - Validate voter eligibility and poll status
    - Prevent duplicate voting
    - Return vote confirmation

12. **GET /api/polls/<id>/results**
    - Return current poll results
    - Include vote counts and percentages
    - Support real-time updates
    - Respect result visibility settings

13. **GET /api/polls/<id>/analytics**
    - Return detailed poll analytics
    - Include voting patterns, demographics, timeline
    - Require poll ownership for detailed data
    - Export capability for data analysis

14. **GET /api/polls/<id>/voters**
    - Return list of voters (admin/owner only)
    - Include voting timestamps and details
    - Support audit and verification

### Poll Discovery Routes

15. **GET /api/polls/my**
    - Return user's created polls
    - Include draft and published polls
    - Support status filtering

16. **GET /api/polls/active**
    - Return currently active polls
    - Filter by end date and status
    - Support category filtering

17. **GET /api/polls/recent**
    - Return recently created or ended polls
    - Time-based filtering
    - Trending polls calculation

18. **GET /api/analytics/summary**
    - Return platform-wide analytics
    - Total polls, votes, active users
    - Trending categories and statistics

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- created_at (TIMESTAMP)
- polls_created (INTEGER DEFAULT 0)
- votes_cast (INTEGER DEFAULT 0)
- is_verified (BOOLEAN DEFAULT FALSE)

Polls table:
- id (TEXT PRIMARY KEY)
- creator_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- poll_type (TEXT) -- 'single', 'multiple', 'ranking'
- created_at (TIMESTAMP)
- end_date (TIMESTAMP)
- is_active (BOOLEAN DEFAULT TRUE)
- is_public (BOOLEAN DEFAULT TRUE)
- allow_multiple_votes (BOOLEAN DEFAULT FALSE)
- require_auth (BOOLEAN DEFAULT TRUE)
- total_votes (INTEGER DEFAULT 0)
- max_votes_per_user (INTEGER DEFAULT 1)

Poll_Options table:
- id (TEXT PRIMARY KEY)
- poll_id (TEXT)
- option_text (TEXT NOT NULL)
- option_order (INTEGER)
- vote_count (INTEGER DEFAULT 0)
- created_at (TIMESTAMP)

Votes table:
- id (TEXT PRIMARY KEY)
- poll_id (TEXT)
- option_id (TEXT)
- voter_id (TEXT) -- null for anonymous
- voter_ip (TEXT)
- user_agent (TEXT)
- voted_at (TIMESTAMP)
- vote_weight (INTEGER DEFAULT 1)

Poll_Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- poll_count (INTEGER DEFAULT 0)

Poll_Settings table:
- poll_id (TEXT PRIMARY KEY)
- settings_json (TEXT) -- JSON object with various settings
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## Polling Features

- **Multiple poll types** (single choice, multiple choice, ranking polls)
- **Time-based poll management** with automatic closure
- **Anonymous and authenticated voting** options
- **Duplicate vote prevention** using multiple strategies
- **Real-time result updates** and calculations
- **Poll privacy controls** (public, private, link-only)
- **Vote verification** and audit capabilities
- **Poll categories** and tagging system

## Vote Security and Validation

- **IP-based duplicate prevention** for anonymous polls
- **User-based voting limits** for authenticated polls
- **Vote integrity checks** using cryptographic hashes
- **Rate limiting** for vote casting
- **Suspicious activity detection** and logging
- **Vote audit trails** for verification
- **Geographic voting restrictions** (optional)

## Analytics and Reporting Features

- **Real-time vote counting** and percentage calculations
- **Voting pattern analysis** and demographics
- **Time-series voting data** for trending analysis
- **Export functionality** for detailed analysis
- **Poll performance metrics** and engagement stats
- **Comparative analytics** across multiple polls
- **Visualization data** for charts and graphs

## Time Management Features

- **Automatic poll closure** at specified end times
- **Timezone support** for global polls
- **Poll duration limits** and validation
- **Early closure** capabilities for poll creators
- **Scheduled poll activation** for future polls
- **Poll extension** functionality (with restrictions)

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, datetime handling, analytics libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Vote validation and fraud prevention
   - Time-based poll management
   - Real-time analytics calculation
   - Security measures for voting integrity
   - Performance optimization for high-volume voting
   - Audit logging for all voting activities
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all polling scenarios including poll creation, secure voting, real-time results, analytics, and time management with proper validation and fraud prevention.