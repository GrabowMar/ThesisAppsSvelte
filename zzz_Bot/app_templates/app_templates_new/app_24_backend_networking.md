# Backend Generation Prompt - Flask Career Networking Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/profiles`, `/api/connections`, `/api/jobs`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Professional Networking System Backend**  
A comprehensive Flask backend for career networking application, featuring professional profile management, connection building, job posting/searching, skill endorsement system, messaging capabilities, and achievement tracking with advanced networking algorithms.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Professional profile creation and management
- Connection request and management system
- Job posting and application tracking
- Skill endorsement and validation system
- Real-time messaging and notifications
- Professional achievements and milestone tracking
- Network analytics and connection insights
- User authentication and privacy controls
- Search and discovery algorithms
- Industry and role categorization
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
import json
import hashlib
import re

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Connection Algorithm Logic
# 5. Search and Discovery
# 6. Messaging System
# 7. API Routes:
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - GET /api/profiles/<id> (get user profile)
#    - PUT /api/profiles/<id> (update profile)
#    - GET /api/profiles/search (search profiles)
#    - GET /api/connections (get user connections)
#    - POST /api/connections/request (send connection request)
#    - PUT /api/connections/<id>/accept (accept connection)
#    - PUT /api/connections/<id>/decline (decline connection)
#    - DELETE /api/connections/<id> (remove connection)
#    - GET /api/connections/suggestions (get connection suggestions)
#    - GET /api/jobs (get job listings)
#    - POST /api/jobs (create job posting)
#    - GET /api/jobs/<id> (get job details)
#    - PUT /api/jobs/<id> (update job posting)
#    - DELETE /api/jobs/<id> (delete job posting)
#    - POST /api/jobs/<id>/apply (apply to job)
#    - GET /api/applications (get user applications)
#    - GET /api/skills (get skills list)
#    - POST /api/skills/endorse (endorse user skill)
#    - GET /api/endorsements (get user endorsements)
#    - GET /api/messages (get conversations)
#    - POST /api/messages (send message)
#    - GET /api/messages/<conversation_id> (get conversation)
#    - GET /api/achievements (get user achievements)
#    - POST /api/achievements (add achievement)
#    - GET /api/feed (get activity feed)
#    - POST /api/posts (create post/update)
#    - GET /api/analytics/network (get network analytics)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, first_name, last_name, industry
   - Validate input and create user account
   - Hash password securely
   - Initialize professional profile
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and network status

3. **POST /api/auth/logout**
   - Clear user session
   - Update last active timestamp
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include profile completion status and network stats

### Profile Management Routes

5. **GET /api/profiles/<id>**
   - Return user profile with professional information
   - Include skills, experience, education, achievements
   - Respect privacy settings and connection status

6. **PUT /api/profiles/<id>**
   - Update user profile information
   - Accept: bio, experience, education, skills, location
   - Require authentication and ownership
   - Return updated profile

7. **GET /api/profiles/search**
   - Search professionals by name, skills, industry, location
   - Support advanced filtering and sorting
   - Return paginated results with relevance scoring

### Connection Management Routes

8. **GET /api/connections**
   - Return user's professional connections
   - Include connection details and mutual connections
   - Support filtering by industry, location, role

9. **POST /api/connections/request**
   - Send connection request to another user
   - Accept: target_user_id, message
   - Validate users and existing connection status
   - Return request confirmation

10. **PUT /api/connections/<id>/accept**
    - Accept incoming connection request
    - Create bidirectional connection
    - Send acceptance notification
    - Return updated connection status

11. **PUT /api/connections/<id>/decline**
    - Decline incoming connection request
    - Update request status
    - Return confirmation

12. **DELETE /api/connections/<id>**
    - Remove existing connection
    - Update connection counts
    - Return confirmation

13. **GET /api/connections/suggestions**
    - Return suggested connections based on network analysis
    - Use mutual connections, industry, skills algorithms
    - Support pagination and refresh

### Job Management Routes

14. **GET /api/jobs**
    - Return job listings with filtering options
    - Support search by title, company, location, skills
    - Include application status for current user

15. **POST /api/jobs**
    - Create new job posting
    - Accept: title, description, company, location, requirements
    - Require authentication
    - Return created job posting

16. **GET /api/jobs/<id>**
    - Return detailed job posting
    - Include application requirements and company info
    - Show application status if user applied

17. **PUT /api/jobs/<id>**
    - Update job posting
    - Require authentication and ownership
    - Return updated job posting

18. **DELETE /api/jobs/<id>**
    - Delete job posting
    - Require authentication and ownership
    - Return confirmation

19. **POST /api/jobs/<id>/apply**
    - Submit job application
    - Accept: cover_letter, resume_url, application_notes
    - Create application record
    - Send notification to job poster

20. **GET /api/applications**
    - Return user's job applications
    - Include application status and dates
    - Support filtering by status and date

### Skill and Endorsement Routes

21. **GET /api/skills**
    - Return comprehensive skills database
    - Support search and categorization
    - Include usage statistics

22. **POST /api/skills/endorse**
    - Endorse another user's skill
    - Accept: user_id, skill_id, endorsement_text
    - Validate connection relationship
    - Return endorsement confirmation

23. **GET /api/endorsements**
    - Return user's skill endorsements
    - Include endorser information and dates
    - Group by skills

### Messaging Routes

24. **GET /api/messages**
    - Return user's message conversations
    - Include last message and unread counts
    - Support search and filtering

25. **POST /api/messages**
    - Send message to connection
    - Accept: recipient_id, message_content, conversation_id
    - Validate connection status
    - Return message confirmation

26. **GET /api/messages/<conversation_id>**
    - Return conversation message history
    - Support pagination for long conversations
    - Mark messages as read

### Achievement and Activity Routes

27. **GET /api/achievements**
    - Return user's professional achievements
    - Include certifications, awards, milestones
    - Support chronological and category views

28. **POST /api/achievements**
    - Add new professional achievement
    - Accept: title, description, date, category, verification
    - Return created achievement

29. **GET /api/feed**
    - Return activity feed from network connections
    - Include job changes, achievements, posts
    - Use relevance algorithm for ordering

30. **POST /api/posts**
    - Create professional update/post
    - Accept: content, post_type, visibility
    - Return created post

31. **GET /api/analytics/network**
    - Return network analytics and insights
    - Include connection growth, industry breakdown
    - Provide networking recommendations

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- first_name (TEXT NOT NULL)
- last_name (TEXT NOT NULL)
- headline (TEXT)
- bio (TEXT)
- industry (TEXT)
- location (TEXT)
- profile_image_url (TEXT)
- created_at (TIMESTAMP)
- last_active (TIMESTAMP)
- connection_count (INTEGER DEFAULT 0)
- profile_views (INTEGER DEFAULT 0)
- is_verified (BOOLEAN DEFAULT FALSE)

Experience table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- company (TEXT NOT NULL)
- position (TEXT NOT NULL)
- description (TEXT)
- start_date (DATE)
- end_date (DATE)
- is_current (BOOLEAN DEFAULT FALSE)
- location (TEXT)

Education table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- institution (TEXT NOT NULL)
- degree (TEXT)
- field_of_study (TEXT)
- start_date (DATE)
- end_date (DATE)
- grade (TEXT)
- activities (TEXT)

Connections table:
- id (TEXT PRIMARY KEY)
- requester_id (TEXT)
- recipient_id (TEXT)
- status (TEXT) -- 'pending', 'accepted', 'declined'
- message (TEXT)
- created_at (TIMESTAMP)
- responded_at (TIMESTAMP)

Skills table:
- id (TEXT PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- category (TEXT)
- description (TEXT)
- usage_count (INTEGER DEFAULT 0)

User_Skills table:
- user_id (TEXT)
- skill_id (TEXT)
- proficiency_level (INTEGER)
- years_experience (INTEGER)
- added_at (TIMESTAMP)
- PRIMARY KEY (user_id, skill_id)

Skill_Endorsements table:
- id (TEXT PRIMARY KEY)
- endorser_id (TEXT)
- endorsee_id (TEXT)
- skill_id (TEXT)
- endorsement_text (TEXT)
- created_at (TIMESTAMP)

Jobs table:
- id (TEXT PRIMARY KEY)
- poster_id (TEXT)
- title (TEXT NOT NULL)
- company (TEXT NOT NULL)
- description (TEXT)
- requirements (TEXT)
- location (TEXT)
- employment_type (TEXT) -- 'full-time', 'part-time', 'contract'
- salary_range (TEXT)
- posted_at (TIMESTAMP)
- expires_at (TIMESTAMP)
- is_active (BOOLEAN DEFAULT TRUE)

Job_Applications table:
- id (TEXT PRIMARY KEY)
- job_id (TEXT)
- applicant_id (TEXT)
- cover_letter (TEXT)
- resume_url (TEXT)
- application_notes (TEXT)
- status (TEXT) -- 'applied', 'reviewed', 'interviewed', 'rejected', 'hired'
- applied_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Messages table:
- id (TEXT PRIMARY KEY)
- conversation_id (TEXT)
- sender_id (TEXT)
- recipient_id (TEXT)
- content (TEXT NOT NULL)
- sent_at (TIMESTAMP)
- read_at (TIMESTAMP)
- message_type (TEXT) -- 'text', 'file', 'system'

Conversations table:
- id (TEXT PRIMARY KEY)
- participant1_id (TEXT)
- participant2_id (TEXT)
- last_message_id (TEXT)
- last_activity (TIMESTAMP)
- created_at (TIMESTAMP)

Achievements table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- achievement_date (DATE)
- category (TEXT) -- 'certification', 'award', 'milestone'
- verification_url (TEXT)
- is_verified (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)

Professional_Posts table:
- id (TEXT PRIMARY KEY)
- author_id (TEXT)
- content (TEXT NOT NULL)
- post_type (TEXT) -- 'update', 'article', 'achievement'
- visibility (TEXT) -- 'public', 'connections', 'private'
- created_at (TIMESTAMP)
- like_count (INTEGER DEFAULT 0)
- comment_count (INTEGER DEFAULT 0)
```

## Networking Algorithm Features

- **Connection suggestion** algorithms based on mutual connections
- **Industry network** analysis and recommendations
- **Skill-based matching** for professional opportunities
- **Geographic networking** with location-based suggestions
- **Career path analysis** and mentorship matching
- **Network strength** scoring and relationship mapping
- **Professional group** recommendations and management
- **Event-based networking** opportunities

## Professional Profile Features

- **Comprehensive profile** with experience, education, skills
- **Portfolio integration** with project showcases
- **Professional summary** with career highlights
- **Skill validation** through endorsements and assessments
- **Achievement tracking** with verification systems
- **Professional photos** and media galleries
- **Contact information** management with privacy controls
- **Profile completion** tracking and optimization tips

## Job Marketplace Features

- **Advanced job search** with multiple filtering options
- **Application tracking** system with status updates
- **Job recommendation** engine based on profile matching
- **Company profile** integration with job postings
- **Salary insights** and market data
- **Application analytics** for job seekers
- **Recruiter tools** for talent discovery
- **Job alert** system with custom criteria

## Messaging and Communication

- **Real-time messaging** between connections
- **Professional etiquette** guidelines and templates
- **File sharing** capabilities for documents and portfolios
- **Group messaging** for professional teams
- **Message encryption** for privacy protection
- **Message search** and organization features
- **Auto-response** and availability status
- **Integration** with email and calendar systems

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, networking algorithms, messaging libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Professional networking algorithms
   - Connection management and privacy
   - Job marketplace functionality
   - Messaging system with real-time capabilities
   - Performance optimization for large networks
   - Privacy and security features
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all professional networking scenarios including profile management, connection building, job marketplace, skill endorsement, and messaging with proper privacy controls and networking algorithms.