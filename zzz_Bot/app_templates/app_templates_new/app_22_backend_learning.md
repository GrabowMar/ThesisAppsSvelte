# Backend Generation Prompt - Flask Language Learning Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/lessons`, `/api/vocabulary`, `/api/progress`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Language Learning System Backend**  
A comprehensive Flask backend for language learning application, featuring lesson management, vocabulary training, grammar exercises, progress tracking, assessment systems, and multilingual content delivery with adaptive learning algorithms.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Comprehensive lesson and course management
- Vocabulary learning with spaced repetition
- Grammar exercises and explanations
- Quiz and assessment system with scoring
- Progress tracking and analytics
- Pronunciation guides and audio handling
- Multilingual content support
- User authentication and profile management
- Achievement and gamification system
- Adaptive learning algorithms
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session, send_file
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
import json
import random
import hashlib

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Learning Algorithm Logic
# 5. Progress Calculation
# 6. Spaced Repetition System
# 7. API Routes:
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - GET /api/languages (get available languages)
#    - GET /api/courses (get available courses)
#    - GET /api/courses/<id> (get course details)
#    - POST /api/courses/<id>/enroll (enroll in course)
#    - GET /api/lessons (get lessons for course)
#    - GET /api/lessons/<id> (get lesson content)
#    - POST /api/lessons/<id>/complete (mark lesson complete)
#    - GET /api/vocabulary (get vocabulary items)
#    - POST /api/vocabulary/<id>/practice (record vocabulary practice)
#    - GET /api/vocabulary/review (get items for review)
#    - GET /api/grammar (get grammar topics)
#    - GET /api/grammar/<id> (get grammar lesson)
#    - POST /api/grammar/<id>/exercise (submit grammar exercise)
#    - GET /api/quizzes (get available quizzes)
#    - GET /api/quizzes/<id> (get quiz questions)
#    - POST /api/quizzes/<id>/submit (submit quiz answers)
#    - GET /api/progress (get user progress)
#    - GET /api/progress/analytics (get detailed analytics)
#    - GET /api/achievements (get user achievements)
#    - GET /api/pronunciation/<word> (get pronunciation guide)
#    - POST /api/pronunciation/check (check pronunciation)
#    - GET /api/translations (get translation exercises)
#    - POST /api/translations/check (check translation)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, native_language
   - Validate input and create user account
   - Hash password securely
   - Initialize learning profile
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and learning status

3. **POST /api/auth/logout**
   - Clear user session
   - Save progress data
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include learning progress and preferences

### Language and Course Management Routes

5. **GET /api/languages**
   - Return list of available languages
   - Include difficulty levels and course counts
   - Support filtering by user's native language

6. **GET /api/courses**
   - Return available courses for selected language
   - Include difficulty levels, duration estimates
   - Support filtering by skill level

7. **GET /api/courses/<id>**
   - Return detailed course information
   - Include lesson list, prerequisites, objectives
   - Show user's enrollment status

8. **POST /api/courses/<id>/enroll**
   - Enroll user in course
   - Set initial progress markers
   - Return enrollment confirmation

### Lesson Management Routes

9. **GET /api/lessons**
   - Return lessons for current course
   - Include completion status and availability
   - Support progressive unlocking

10. **GET /api/lessons/<id>**
    - Return lesson content and materials
    - Include text, audio files, exercises
    - Track lesson access

11. **POST /api/lessons/<id>/complete**
    - Mark lesson as completed
    - Update progress tracking
    - Unlock next lessons
    - Return completion status

### Vocabulary System Routes

12. **GET /api/vocabulary**
    - Return vocabulary items for current level
    - Include translations, examples, difficulty
    - Support filtering by topic/category

13. **POST /api/vocabulary/<id>/practice**
    - Record vocabulary practice session
    - Accept: user_answer, response_time, difficulty
    - Update spaced repetition schedule
    - Return feedback and next review date

14. **GET /api/vocabulary/review**
    - Return vocabulary items due for review
    - Use spaced repetition algorithm
    - Prioritize by difficulty and retention

### Grammar System Routes

15. **GET /api/grammar**
    - Return grammar topics for current level
    - Include explanations and examples
    - Show progress status

16. **GET /api/grammar/<id>**
    - Return detailed grammar lesson
    - Include rules, examples, exercises
    - Provide interactive content

17. **POST /api/grammar/<id>/exercise**
    - Submit grammar exercise answers
    - Accept: answers array, time_spent
    - Provide immediate feedback
    - Update progress tracking

### Assessment and Quiz Routes

18. **GET /api/quizzes**
    - Return available quizzes for user level
    - Include quiz types and difficulty
    - Show completion history

19. **GET /api/quizzes/<id>**
    - Return quiz questions
    - Support multiple question types
    - Randomize question order

20. **POST /api/quizzes/<id>/submit**
    - Submit quiz answers
    - Calculate scores and feedback
    - Update user performance metrics
    - Return detailed results

### Progress and Analytics Routes

21. **GET /api/progress**
    - Return user's learning progress
    - Include completion percentages, streaks
    - Show skill level improvements

22. **GET /api/progress/analytics**
    - Return detailed learning analytics
    - Include time spent, accuracy rates
    - Provide performance insights

23. **GET /api/achievements**
    - Return user achievements and badges
    - Include progress toward goals
    - Show leaderboard information

### Pronunciation and Audio Routes

24. **GET /api/pronunciation/<word>**
    - Return pronunciation guide for word
    - Include phonetic transcription
    - Provide audio file URL

25. **POST /api/pronunciation/check**
    - Check user pronunciation (mock)
    - Accept: audio_data, target_word
    - Return accuracy score and feedback

### Translation Routes

26. **GET /api/translations**
    - Return translation exercises
    - Include sentences and phrases
    - Support multiple difficulty levels

27. **POST /api/translations/check**
    - Check translation accuracy
    - Accept: user_translation, source_text
    - Return feedback and corrections

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- native_language (TEXT)
- target_languages (TEXT) -- JSON array
- created_at (TIMESTAMP)
- last_active (TIMESTAMP)
- total_study_time (INTEGER DEFAULT 0)
- current_streak (INTEGER DEFAULT 0)
- longest_streak (INTEGER DEFAULT 0)

Languages table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- code (TEXT UNIQUE NOT NULL) -- ISO 639-1
- difficulty_level (INTEGER)
- course_count (INTEGER DEFAULT 0)
- active_learners (INTEGER DEFAULT 0)

Courses table:
- id (TEXT PRIMARY KEY)
- language_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- difficulty_level (INTEGER)
- estimated_duration (INTEGER) -- hours
- lesson_count (INTEGER)
- prerequisite_course_id (TEXT)
- created_at (TIMESTAMP)

Lessons table:
- id (TEXT PRIMARY KEY)
- course_id (TEXT)
- title (TEXT NOT NULL)
- content (TEXT) -- JSON content
- lesson_order (INTEGER)
- lesson_type (TEXT) -- 'vocabulary', 'grammar', 'conversation'
- estimated_duration (INTEGER) -- minutes
- audio_file_url (TEXT)
- created_at (TIMESTAMP)

Vocabulary table:
- id (TEXT PRIMARY KEY)
- language_id (TEXT)
- word (TEXT NOT NULL)
- translation (TEXT NOT NULL)
- pronunciation (TEXT)
- example_sentence (TEXT)
- difficulty_level (INTEGER)
- category (TEXT)
- audio_file_url (TEXT)
- created_at (TIMESTAMP)

User_Vocabulary table:
- user_id (TEXT)
- vocabulary_id (TEXT)
- familiarity_level (INTEGER DEFAULT 0)
- last_reviewed (TIMESTAMP)
- next_review (TIMESTAMP)
- review_count (INTEGER DEFAULT 0)
- correct_count (INTEGER DEFAULT 0)
- PRIMARY KEY (user_id, vocabulary_id)

Grammar_Topics table:
- id (TEXT PRIMARY KEY)
- language_id (TEXT)
- title (TEXT NOT NULL)
- explanation (TEXT)
- examples (TEXT) -- JSON array
- difficulty_level (INTEGER)
- category (TEXT)

User_Progress table:
- user_id (TEXT)
- course_id (TEXT)
- lessons_completed (INTEGER DEFAULT 0)
- total_lessons (INTEGER)
- completion_percentage (DECIMAL)
- last_lesson_id (TEXT)
- started_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- PRIMARY KEY (user_id, course_id)

Quizzes table:
- id (TEXT PRIMARY KEY)
- course_id (TEXT)
- title (TEXT NOT NULL)
- quiz_type (TEXT) -- 'vocabulary', 'grammar', 'comprehensive'
- questions (TEXT) -- JSON array
- difficulty_level (INTEGER)
- time_limit (INTEGER) -- minutes
- max_attempts (INTEGER DEFAULT 3)

Quiz_Attempts table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- quiz_id (TEXT)
- score (DECIMAL)
- max_score (DECIMAL)
- answers (TEXT) -- JSON array
- time_taken (INTEGER) -- seconds
- completed_at (TIMESTAMP)

Achievements table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- icon_url (TEXT)
- criteria (TEXT) -- JSON object
- points (INTEGER)
- category (TEXT)

User_Achievements table:
- user_id (TEXT)
- achievement_id (TEXT)
- earned_at (TIMESTAMP)
- PRIMARY KEY (user_id, achievement_id)
```

## Learning Algorithm Features

- **Spaced repetition system** for vocabulary retention
- **Adaptive difficulty** based on user performance
- **Personalized learning paths** with skill assessment
- **Progress analytics** with performance insights
- **Streak tracking** and motivation systems
- **Intelligent review scheduling** based on forgetting curves
- **Skill level assessment** and placement testing
- **Learning goal setting** and achievement tracking

## Content Management Features

- **Multilingual content** support with localization
- **Audio pronunciation** guides and examples
- **Interactive exercises** with immediate feedback
- **Grammar explanations** with contextual examples
- **Cultural context** and usage notes
- **Progressive content** unlocking based on mastery
- **Custom lesson** creation and management
- **Content difficulty** assessment and tagging

## Assessment and Feedback System

- **Multiple question types** (multiple choice, fill-in-blank, audio)
- **Immediate feedback** with explanations
- **Performance analytics** and progress tracking
- **Adaptive testing** based on user ability
- **Comprehensive assessments** for skill certification
- **Error pattern analysis** for targeted practice
- **Pronunciation evaluation** with feedback
- **Writing assessment** with grammar checking

## Gamification Features

- **Achievement system** with badges and rewards
- **Progress streaks** and daily goals
- **Leaderboards** and social competition
- **Experience points** and level progression
- **Challenge modes** and time-based exercises
- **Social features** for practice partners
- **Goal setting** and milestone tracking

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, audio processing, language detection libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Learning algorithm implementation
   - Progress tracking and analytics
   - Multilingual content support
   - Audio file management
   - Performance optimization for learning data
   - Spaced repetition algorithms
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all language learning scenarios including lesson management, vocabulary training, progress tracking, and assessment systems with proper educational algorithms and user engagement features.