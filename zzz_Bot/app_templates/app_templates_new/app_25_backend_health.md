# Backend Generation Prompt - Flask Mental Health Tracking Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/mood`, `/api/journal`, `/api/wellness`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Mental Wellness Tracking System Backend**  
A comprehensive Flask backend for mental health application, featuring mood tracking, stress monitoring, journaling, wellness strategies, progress analytics, self-care management, and professional resource integration with privacy-focused design and crisis support.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Comprehensive mood and emotion tracking system
- Stress level monitoring with pattern analysis
- Secure journaling with privacy controls
- Evidence-based coping strategy recommendations
- Progress visualization and wellness analytics
- Self-care reminder and notification system
- Professional resource directory and crisis support
- User authentication with privacy protection
- Data encryption for sensitive mental health information
- Wellness goal setting and achievement tracking
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
from cryptography.fernet import Fernet
import base64

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'
app.config['ENCRYPTION_KEY'] = Fernet.generate_key()

# 3. Database Models/Setup
# 4. Mood Analysis Logic
# 5. Wellness Algorithms
# 6. Crisis Detection
# 7. API Routes:
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - POST /api/mood/track (record mood entry)
#    - GET /api/mood/history (get mood history)
#    - GET /api/mood/insights (get mood patterns and insights)
#    - POST /api/stress/track (record stress level)
#    - GET /api/stress/history (get stress tracking data)
#    - GET /api/stress/analysis (get stress pattern analysis)
#    - POST /api/journal/entry (create journal entry)
#    - GET /api/journal/entries (get journal entries)
#    - PUT /api/journal/entry/<id> (update journal entry)
#    - DELETE /api/journal/entry/<id> (delete journal entry)
#    - GET /api/coping/strategies (get personalized coping strategies)
#    - POST /api/coping/rate (rate strategy effectiveness)
#    - GET /api/wellness/progress (get wellness progress data)
#    - GET /api/wellness/goals (get wellness goals)
#    - POST /api/wellness/goals (create wellness goal)
#    - PUT /api/wellness/goals/<id> (update goal progress)
#    - GET /api/reminders (get self-care reminders)
#    - POST /api/reminders (create reminder)
#    - PUT /api/reminders/<id> (update reminder)
#    - DELETE /api/reminders/<id> (delete reminder)
#    - GET /api/resources (get professional resources)
#    - GET /api/resources/crisis (get crisis support resources)
#    - POST /api/check-in (daily wellness check-in)
#    - GET /api/analytics/dashboard (get wellness dashboard data)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, timezone, crisis_contact
   - Validate input and create user account
   - Hash password securely
   - Initialize wellness profile and privacy settings
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and wellness status

3. **POST /api/auth/logout**
   - Clear user session
   - Save any pending wellness data
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include wellness preferences and privacy settings

### Mood Tracking Routes

5. **POST /api/mood/track**
   - Record mood entry with timestamp
   - Accept: mood_rating, energy_level, emotions, triggers, notes
   - Encrypt sensitive data before storage
   - Return mood entry confirmation

6. **GET /api/mood/history**
   - Return user's mood tracking history
   - Support date range filtering and pagination
   - Include mood trends and patterns

7. **GET /api/mood/insights**
   - Return mood pattern analysis and insights
   - Include trigger identification and trend analysis
   - Provide personalized recommendations

### Stress Monitoring Routes

8. **POST /api/stress/track**
   - Record stress level entry
   - Accept: stress_level, stressors, physical_symptoms, coping_used
   - Analyze stress patterns
   - Return stress tracking confirmation

9. **GET /api/stress/history**
   - Return stress tracking data with visualization
   - Include stress level trends and correlations
   - Support filtering by date and stress factors

10. **GET /api/stress/analysis**
    - Return comprehensive stress pattern analysis
    - Include stressor identification and coping effectiveness
    - Provide stress management recommendations

### Journaling Routes

11. **POST /api/journal/entry**
    - Create encrypted journal entry
    - Accept: title, content, mood_tag, privacy_level, tags
    - Encrypt content for privacy protection
    - Return entry confirmation

12. **GET /api/journal/entries**
    - Return user's journal entries (decrypted)
    - Support filtering by date, mood, tags
    - Include entry metadata and insights

13. **PUT /api/journal/entry/<id>**
    - Update journal entry
    - Re-encrypt updated content
    - Return updated entry confirmation

14. **DELETE /api/journal/entry/<id>**
    - Securely delete journal entry
    - Clear encrypted data
    - Return deletion confirmation

### Coping Strategies Routes

15. **GET /api/coping/strategies**
    - Return personalized coping strategies
    - Base recommendations on user's mood patterns
    - Include evidence-based techniques

16. **POST /api/coping/rate**
    - Rate effectiveness of coping strategy
    - Accept: strategy_id, effectiveness_rating, notes
    - Update strategy recommendations
    - Return rating confirmation

### Wellness Progress Routes

17. **GET /api/wellness/progress**
    - Return comprehensive wellness progress data
    - Include mood trends, stress patterns, goal progress
    - Generate wellness insights and recommendations

18. **GET /api/wellness/goals**
    - Return user's wellness goals
    - Include progress tracking and milestones
    - Show achievement status

19. **POST /api/wellness/goals**
    - Create new wellness goal
    - Accept: goal_type, target, timeframe, strategies
    - Return created goal

20. **PUT /api/wellness/goals/<id>**
    - Update goal progress
    - Accept: progress_update, notes, milestone_reached
    - Return updated goal status

### Self-Care Reminder Routes

21. **GET /api/reminders**
    - Return user's self-care reminders
    - Include scheduled and recurring reminders
    - Show completion status

22. **POST /api/reminders**
    - Create self-care reminder
    - Accept: reminder_type, schedule, message, priority
    - Return created reminder

23. **PUT /api/reminders/<id>**
    - Update reminder settings or mark complete
    - Return updated reminder status

24. **DELETE /api/reminders/<id>**
    - Delete self-care reminder
    - Return deletion confirmation

### Professional Resources Routes

25. **GET /api/resources**
    - Return directory of mental health resources
    - Include therapists, support groups, helplines
    - Support filtering by location and specialty

26. **GET /api/resources/crisis**
    - Return immediate crisis support resources
    - Include emergency contacts and hotlines
    - Provide location-based emergency services

### Wellness Check-in Routes

27. **POST /api/check-in**
    - Record daily wellness check-in
    - Accept: overall_rating, sleep_quality, energy, social_connection
    - Update wellness tracking
    - Return check-in summary

28. **GET /api/analytics/dashboard**
    - Return wellness dashboard data
    - Include recent trends, achievements, recommendations
    - Generate personalized insights

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- timezone (TEXT)
- crisis_contact (TEXT)
- privacy_level (TEXT DEFAULT 'high')
- created_at (TIMESTAMP)
- last_check_in (TIMESTAMP)
- wellness_score (INTEGER DEFAULT 50)
- encryption_key (TEXT)

Mood_Entries table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- mood_rating (INTEGER) -- 1-10 scale
- energy_level (INTEGER) -- 1-10 scale
- emotions (TEXT) -- JSON array
- triggers (TEXT) -- JSON array
- notes (TEXT) -- encrypted
- recorded_at (TIMESTAMP)
- created_at (TIMESTAMP)

Stress_Entries table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- stress_level (INTEGER) -- 1-10 scale
- stressors (TEXT) -- JSON array
- physical_symptoms (TEXT) -- JSON array
- coping_strategies_used (TEXT) -- JSON array
- effectiveness_rating (INTEGER)
- recorded_at (TIMESTAMP)
- created_at (TIMESTAMP)

Journal_Entries table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- title (TEXT)
- content (TEXT) -- encrypted
- mood_tag (TEXT)
- privacy_level (TEXT)
- tags (TEXT) -- JSON array
- word_count (INTEGER)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Coping_Strategies table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- category (TEXT) -- 'breathing', 'mindfulness', 'physical', 'social'
- instructions (TEXT)
- duration_minutes (INTEGER)
- evidence_level (TEXT) -- 'high', 'medium', 'low'

User_Strategy_Ratings table:
- user_id (TEXT)
- strategy_id (TEXT)
- effectiveness_rating (INTEGER) -- 1-5 scale
- usage_count (INTEGER DEFAULT 0)
- last_used (TIMESTAMP)
- notes (TEXT)
- PRIMARY KEY (user_id, strategy_id)

Wellness_Goals table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- goal_type (TEXT) -- 'mood_stability', 'stress_reduction', 'sleep_improvement'
- title (TEXT NOT NULL)
- description (TEXT)
- target_value (INTEGER)
- current_progress (INTEGER DEFAULT 0)
- target_date (DATE)
- is_achieved (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)

Self_Care_Reminders table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- reminder_type (TEXT) -- 'medication', 'exercise', 'meditation', 'social'
- title (TEXT NOT NULL)
- message (TEXT)
- schedule_type (TEXT) -- 'daily', 'weekly', 'custom'
- schedule_time (TIME)
- is_active (BOOLEAN DEFAULT TRUE)
- last_completed (TIMESTAMP)
- created_at (TIMESTAMP)

Professional_Resources table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- resource_type (TEXT) -- 'therapist', 'crisis_line', 'support_group'
- description (TEXT)
- contact_info (TEXT)
- location (TEXT)
- specialty (TEXT)
- availability (TEXT)
- is_crisis_resource (BOOLEAN DEFAULT FALSE)

Daily_Check_Ins table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- overall_rating (INTEGER) -- 1-10 scale
- sleep_quality (INTEGER) -- 1-10 scale
- energy_level (INTEGER) -- 1-10 scale
- social_connection (INTEGER) -- 1-10 scale
- gratitude_note (TEXT)
- check_in_date (DATE)
- created_at (TIMESTAMP)

Wellness_Insights table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- insight_type (TEXT) -- 'pattern', 'recommendation', 'achievement'
- title (TEXT)
- description (TEXT)
- confidence_score (DECIMAL)
- is_read (BOOLEAN DEFAULT FALSE)
- generated_at (TIMESTAMP)
```

## Mental Health Features

- **Mood pattern analysis** with trigger identification
- **Stress correlation** tracking and management
- **Evidence-based interventions** and coping strategies
- **Crisis detection** algorithms with automatic resource provision
- **Wellness goal** setting and achievement tracking
- **Daily check-in** systems with progress monitoring
- **Mindfulness integration** with guided exercises
- **Sleep and lifestyle** factor correlation analysis

## Privacy and Security Features

- **End-to-end encryption** for journal entries and sensitive data
- **Data anonymization** for analytics while preserving privacy
- **Granular privacy controls** for data sharing preferences
- **Secure authentication** with mental health considerations
- **Crisis contact** integration for emergency situations
- **Data retention policies** with user control
- **HIPAA-inspired** privacy protections
- **Export and deletion** rights for user data

## Wellness Algorithm Features

- **Personalized recommendations** based on individual patterns
- **Evidence-based interventions** from clinical research
- **Adaptive reminders** based on user engagement
- **Progress tracking** with meaningful metrics
- **Goal adjustment** algorithms for realistic target setting
- **Crisis risk assessment** with appropriate escalation
- **Wellness scoring** with holistic health indicators
- **Intervention timing** optimization for maximum effectiveness

## Professional Integration Features

- **Resource directory** with verified mental health professionals
- **Crisis support** with immediate access to help
- **Therapist communication** tools (referral preparation)
- **Progress sharing** options for healthcare providers
- **Assessment tools** for professional evaluation
- **Treatment adherence** tracking and reminders
- **Safety planning** integration and crisis management
- **Professional dashboard** for authorized healthcare providers

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, cryptography, mental health analysis libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Mental health data encryption and privacy
   - Crisis detection and intervention algorithms
   - Evidence-based wellness recommendations
   - Progress tracking and analytics
   - Performance optimization for sensitive data
   - Professional resource integration
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all mental wellness scenarios including mood tracking, crisis support, professional resource access, and secure journaling with proper privacy protection and evidence-based interventions.