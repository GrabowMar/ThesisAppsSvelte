# Backend Generation Prompt - Flask Fitness Logger Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/workouts`, `/api/exercises`, `/api/progress`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Fitness Logger System Backend**  
A comprehensive Flask backend for fitness tracking application, featuring workout logging, exercise management, progress tracking, statistics calculation, goal setting, and performance analytics with comprehensive data management.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete workout logging and session management
- Exercise library with detailed information and instructions
- Progress tracking with measurements and performance metrics
- Advanced statistics calculation and analytics
- Goal setting and achievement tracking
- Personal records and milestone management
- Nutrition logging and calorie tracking
- User authentication and profile management
- Data visualization support for charts and graphs
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
from statistics import mean, median
import math

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Statistics Calculation Logic
# 5. Progress Analysis
# 6. Goal Management
# 7. API Routes:
#    - GET /api/workouts (list workouts)
#    - GET /api/workouts/<id> (get workout details)
#    - POST /api/workouts (create workout)
#    - PUT /api/workouts/<id> (update workout)
#    - DELETE /api/workouts/<id> (delete workout)
#    - GET /api/exercises (get exercise library)
#    - GET /api/exercises/<id> (get exercise details)
#    - POST /api/exercises (create custom exercise)
#    - GET /api/progress (get progress data)
#    - POST /api/progress (log progress measurement)
#    - GET /api/statistics (get workout statistics)
#    - GET /api/goals (get goals)
#    - POST /api/goals (create goal)
#    - PUT /api/goals/<id> (update goal)
#    - DELETE /api/goals/<id> (delete goal)
#    - GET /api/records (get personal records)
#    - GET /api/nutrition (get nutrition logs)
#    - POST /api/nutrition (log nutrition)
#    - GET /api/analytics (get detailed analytics)
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
   - Accept: username, email, password, fitness_goals, experience_level
   - Validate input and create user account
   - Initialize user fitness profile
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and fitness stats

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include fitness profile and preferences

### Workout Management Routes

5. **GET /api/workouts**
   - Return list of user's workouts
   - Support filtering by date, type, muscle group
   - Include workout summaries and statistics
   - Support pagination for large datasets

6. **GET /api/workouts/<id>**
   - Return specific workout with full details
   - Include exercises, sets, reps, weights, and timing
   - Show workout notes and performance metrics

7. **POST /api/workouts**
   - Create new workout session
   - Accept: name, date, exercises, duration, notes
   - Calculate workout statistics and calories burned
   - Return created workout with generated metrics

8. **PUT /api/workouts/<id>**
   - Update existing workout
   - Accept: exercises, sets, reps, weights, notes
   - Recalculate statistics and personal records
   - Return updated workout

9. **DELETE /api/workouts/<id>**
   - Delete workout session
   - Update related statistics and progress data
   - Return confirmation

### Exercise Library Routes

10. **GET /api/exercises**
    - Return exercise library with filtering
    - Support filtering by muscle group, equipment, difficulty
    - Include exercise descriptions and instructions
    - Support search functionality

11. **GET /api/exercises/<id>**
    - Return specific exercise details
    - Include instructions, muscle groups, equipment needed
    - Show user's history with this exercise

12. **POST /api/exercises**
    - Create custom exercise
    - Accept: name, description, muscle_groups, equipment
    - Validate exercise data
    - Return created exercise

### Progress Tracking Routes

13. **GET /api/progress**
    - Return user's progress measurements
    - Include weight, body fat, measurements, photos
    - Support date range filtering
    - Calculate progress trends

14. **POST /api/progress**
    - Log new progress measurement
    - Accept: weight, body_fat, measurements, notes, photo_url
    - Calculate changes and trends
    - Return updated progress data

15. **GET /api/statistics**
    - Return comprehensive workout statistics
    - Include volume, frequency, personal records
    - Calculate weekly/monthly/yearly summaries
    - Show muscle group distribution

### Goal Management Routes

16. **GET /api/goals**
    - Return user's fitness goals
    - Include progress towards goals
    - Show achieved and active goals
    - Calculate goal completion percentages

17. **POST /api/goals**
    - Create new fitness goal
    - Accept: type, target_value, target_date, description
    - Validate goal parameters
    - Return created goal

18. **PUT /api/goals/<id>**
    - Update existing goal
    - Accept: target_value, target_date, status
    - Recalculate progress and timeline
    - Return updated goal

19. **DELETE /api/goals/<id>**
    - Delete goal
    - Clean up related tracking data
    - Return confirmation

### Analytics and Records Routes

20. **GET /api/records**
    - Return personal records and achievements
    - Include best lifts, longest runs, etc.
    - Show record progression over time
    - Calculate strength ratios and rankings

21. **GET /api/nutrition**
    - Return nutrition logs and meal tracking
    - Include calorie intake, macronutrients
    - Support date range filtering
    - Calculate nutritional statistics

22. **POST /api/nutrition**
    - Log nutrition data
    - Accept: meals, calories, macronutrients, water_intake
    - Calculate daily nutritional totals
    - Return logged nutrition data

23. **GET /api/analytics**
    - Return detailed fitness analytics
    - Include workout trends, progress patterns
    - Calculate performance metrics and insights
    - Generate chart data for visualizations

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- height (DECIMAL)
- age (INTEGER)
- gender (TEXT)
- fitness_level (TEXT)
- created_at (TIMESTAMP)
- last_workout (TIMESTAMP)

Workouts table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT)
- date (DATE)
- start_time (TIMESTAMP)
- end_time (TIMESTAMP)
- duration (INTEGER) -- minutes
- total_volume (DECIMAL)
- calories_burned (INTEGER)
- notes (TEXT)
- created_at (TIMESTAMP)

Exercises table:
- id (TEXT PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- muscle_groups (TEXT) -- JSON array
- equipment (TEXT) -- JSON array
- difficulty_level (TEXT)
- instructions (TEXT)
- is_custom (BOOLEAN DEFAULT FALSE)
- created_by (TEXT)

Workout_Exercises table:
- id (TEXT PRIMARY KEY)
- workout_id (TEXT)
- exercise_id (TEXT)
- sets (INTEGER)
- reps (TEXT) -- JSON array for each set
- weight (TEXT) -- JSON array for each set
- rest_time (INTEGER)
- notes (TEXT)
- order_index (INTEGER)

Progress_Logs table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- date (DATE)
- weight (DECIMAL)
- body_fat_percentage (DECIMAL)
- muscle_mass (DECIMAL)
- measurements (TEXT) -- JSON object
- notes (TEXT)
- photo_url (TEXT)

Goals table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- goal_type (TEXT) -- 'weight_loss', 'strength', 'endurance', etc.
- target_value (DECIMAL)
- current_value (DECIMAL)
- target_date (DATE)
- status (TEXT) -- 'active', 'completed', 'paused'
- description (TEXT)
- created_at (TIMESTAMP)

Personal_Records table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- exercise_id (TEXT)
- record_type (TEXT) -- '1RM', 'volume', 'reps', 'distance', 'time'
- value (DECIMAL)
- date_achieved (DATE)
- workout_id (TEXT)

Nutrition_Logs table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- date (DATE)
- meal_type (TEXT) -- 'breakfast', 'lunch', 'dinner', 'snack'
- food_items (TEXT) -- JSON array
- calories (INTEGER)
- protein (DECIMAL)
- carbs (DECIMAL)
- fat (DECIMAL)
- water_intake (DECIMAL)
```

## Fitness Tracking Features

- **Comprehensive workout logging** with exercises, sets, reps, weights
- **Exercise library** with detailed instructions and muscle group targeting
- **Progress tracking** with body measurements and photo comparisons
- **Personal records** tracking and achievement notifications
- **Goal setting** with progress monitoring and deadline tracking
- **Workout templates** for routine planning and consistency
- **Rest period timing** and workout duration tracking
- **Volume load calculations** and intensity metrics

## Statistics and Analytics Features

- **Workout frequency** and consistency analysis
- **Volume progression** tracking over time
- **Strength gain calculations** and trend analysis
- **Muscle group balance** assessment and recommendations
- **Calorie burn estimation** based on workout intensity
- **Performance ratios** and strength standards comparison
- **Weekly/monthly summaries** with key performance indicators
- **Comparative analytics** against previous periods

## Progress Monitoring Features

- **Body composition tracking** with multiple measurement points
- **Weight progression** with trend analysis and predictions
- **Photo progress** comparison with before/after galleries
- **Measurement tracking** for various body parts
- **Performance metrics** improvement over time
- **Goal achievement** tracking with milestone celebrations
- **Plateau detection** and breakthrough recommendations
- **Motivation tracking** with mood and energy levels

## Nutrition Integration Features

- **Calorie tracking** with macronutrient breakdown
- **Meal logging** with portion size estimation
- **Water intake** monitoring and hydration tracking
- **Nutritional goal** setting and progress monitoring
- **Macro ratio** optimization for fitness goals
- **Supplement tracking** and timing recommendations
- **Integration with workout** performance correlation
- **Weekly nutrition** summaries and trend analysis

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, statistics libraries, datetime handling

3. **Production Ready Features**
   - Comprehensive error handling
   - Data validation and integrity checks
   - Statistical calculation accuracy
   - Performance optimization for analytics
   - Goal tracking and notification system
   - Progress analysis and trend detection
   - Personal record validation and updates
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all fitness tracking scenarios including workout logging, progress monitoring, goal management, and analytics with proper validation and statistical accuracy.