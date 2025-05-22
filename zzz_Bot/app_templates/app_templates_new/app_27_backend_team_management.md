# Backend Generation Prompt - Flask Sports Team Management Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/players`, `/api/matches`, `/api/training`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Sports Team Management System Backend**  
A comprehensive Flask backend for sports team management application, featuring player roster management, performance tracking, training schedule coordination, match planning, statistical analysis, injury monitoring, and team communication with advanced sports analytics and team coordination tools.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Comprehensive player roster and profile management
- Performance tracking and statistical analysis
- Training schedule creation and management
- Match/game planning and coordination
- Advanced statistical analysis and reporting
- Injury and health monitoring systems
- Team communication and messaging tools
- User authentication with role-based access (coach, player, staff)
- Sports analytics and performance insights
- Equipment and facility management
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
from decimal import Decimal

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Performance Analytics
# 5. Statistics Calculation
# 6. Team Management Logic
# 7. API Routes:
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - GET /api/players (get team roster)
#    - POST /api/players (add new player)
#    - GET /api/players/<id> (get player details)
#    - PUT /api/players/<id> (update player info)
#    - DELETE /api/players/<id> (remove player)
#    - POST /api/performance/track (record performance data)
#    - GET /api/performance/<player_id> (get player performance)
#    - GET /api/performance/team (get team performance analytics)
#    - GET /api/training/schedule (get training schedule)
#    - POST /api/training/schedule (create training session)
#    - PUT /api/training/<id> (update training session)
#    - DELETE /api/training/<id> (cancel training session)
#    - POST /api/training/<id>/attendance (mark attendance)
#    - GET /api/matches (get match schedule)
#    - POST /api/matches (create match/game)
#    - GET /api/matches/<id> (get match details)
#    - PUT /api/matches/<id> (update match info)
#    - POST /api/matches/<id>/lineup (set match lineup)
#    - POST /api/matches/<id>/stats (record match statistics)
#    - GET /api/injuries (get injury reports)
#    - POST /api/injuries (report injury)
#    - PUT /api/injuries/<id> (update injury status)
#    - GET /api/health/<player_id> (get player health status)
#    - POST /api/health/checkup (record health checkup)
#    - GET /api/messages (get team messages)
#    - POST /api/messages (send team message)
#    - GET /api/analytics/team (get team analytics)
#    - GET /api/analytics/player/<id> (get player analytics)
#    - GET /api/equipment (get equipment inventory)
#    - POST /api/equipment (add equipment)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, role, team_id
   - Validate input and create user account
   - Hash password securely
   - Initialize user profile based on role
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and team access level

3. **POST /api/auth/logout**
   - Clear user session
   - Save pending team data
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include role permissions and team associations

### Player Management Routes

5. **GET /api/players**
   - Return team roster with player profiles
   - Include basic stats, position, status
   - Support filtering by position, status, availability

6. **POST /api/players**
   - Add new player to team roster
   - Accept: name, position, jersey_number, contact_info, medical_info
   - Validate jersey number uniqueness
   - Return created player profile

7. **GET /api/players/<id>**
   - Return detailed player profile
   - Include performance history, health status, contract info
   - Show training attendance and match participation

8. **PUT /api/players/<id>**
   - Update player information
   - Accept: position, jersey_number, status, contact_info
   - Require appropriate permissions
   - Return updated player profile

9. **DELETE /api/players/<id>**
   - Remove player from roster
   - Handle historical data preservation
   - Require coach/admin permissions
   - Return confirmation

### Performance Tracking Routes

10. **POST /api/performance/track**
    - Record player performance metrics
    - Accept: player_id, metric_type, value, date, notes
    - Calculate performance trends
    - Return performance entry confirmation

11. **GET /api/performance/<player_id>**
    - Return player's performance history
    - Include trends, improvements, benchmarks
    - Support date range filtering

12. **GET /api/performance/team**
    - Return team-wide performance analytics
    - Include averages, top performers, areas for improvement
    - Generate insights and recommendations

### Training Management Routes

13. **GET /api/training/schedule**
    - Return training schedule with details
    - Include upcoming sessions, recurring training
    - Show attendance requirements and player availability

14. **POST /api/training/schedule**
    - Create new training session
    - Accept: date, time, duration, type, location, focus_areas
    - Check facility and coach availability
    - Return created training session

15. **PUT /api/training/<id>**
    - Update training session details
    - Accept: date, time, location, focus_areas, notes
    - Notify affected players
    - Return updated session

16. **DELETE /api/training/<id>**
    - Cancel training session
    - Send cancellation notifications
    - Return confirmation

17. **POST /api/training/<id>/attendance**
    - Mark player attendance for training
    - Accept: player_id, attendance_status, performance_notes
    - Update attendance records
    - Return attendance confirmation

### Match Management Routes

18. **GET /api/matches**
    - Return match schedule and results
    - Include upcoming games, past results
    - Support filtering by season, opponent, home/away

19. **POST /api/matches**
    - Create new match/game
    - Accept: opponent, date, time, location, match_type
    - Check player and facility availability
    - Return created match

20. **GET /api/matches/<id>**
    - Return detailed match information
    - Include lineup, statistics, match events
    - Show player performance data

21. **PUT /api/matches/<id>**
    - Update match details
    - Accept: date, time, location, lineup, score
    - Return updated match info

22. **POST /api/matches/<id>/lineup**
    - Set match lineup and formations
    - Accept: starting_lineup, substitutes, formation
    - Validate player availability
    - Return lineup confirmation

23. **POST /api/matches/<id>/stats**
    - Record match statistics
    - Accept: player_stats, team_stats, match_events
    - Calculate team and individual performance metrics
    - Return statistics summary

### Health and Injury Management Routes

24. **GET /api/injuries**
    - Return injury reports and status
    - Include current injuries, recovery timelines
    - Support filtering by severity, player, status

25. **POST /api/injuries**
    - Report new injury
    - Accept: player_id, injury_type, severity, description, date
    - Create recovery plan
    - Return injury report

26. **PUT /api/injuries/<id>**
    - Update injury status and recovery progress
    - Accept: status, recovery_notes, return_date
    - Update player availability
    - Return updated injury report

27. **GET /api/health/<player_id>**
    - Return player's health status and history
    - Include fitness levels, medical clearances
    - Show injury history and risk factors

28. **POST /api/health/checkup**
    - Record health checkup results
    - Accept: player_id, checkup_type, results, recommendations
    - Update health status
    - Return checkup summary

### Communication Routes

29. **GET /api/messages**
    - Return team messages and announcements
    - Include coaching staff communications
    - Support filtering by type, urgency, date

30. **POST /api/messages**
    - Send message to team or individuals
    - Accept: recipients, subject, content, priority
    - Support attachments and notifications
    - Return message confirmation

### Analytics and Reporting Routes

31. **GET /api/analytics/team**
    - Return comprehensive team analytics
    - Include performance trends, strengths, weaknesses
    - Provide strategic insights and recommendations

32. **GET /api/analytics/player/<id>**
    - Return detailed player analytics
    - Include performance metrics, improvement areas
    - Compare with team and league averages

33. **GET /api/equipment**
    - Return equipment inventory and status
    - Include availability, condition, assignments
    - Support equipment tracking and maintenance

34. **POST /api/equipment**
    - Add equipment to inventory
    - Accept: equipment_type, quantity, condition, location
    - Return equipment entry

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- role (TEXT) -- 'coach', 'player', 'staff', 'admin'
- team_id (TEXT)
- created_at (TIMESTAMP)
- last_active (TIMESTAMP)

Teams table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- sport (TEXT NOT NULL)
- season (TEXT)
- league (TEXT)
- home_venue (TEXT)
- created_at (TIMESTAMP)

Players table:
- id (TEXT PRIMARY KEY)
- team_id (TEXT)
- user_id (TEXT)
- first_name (TEXT NOT NULL)
- last_name (TEXT NOT NULL)
- jersey_number (INTEGER)
- position (TEXT)
- date_of_birth (DATE)
- height (INTEGER) -- in cm
- weight (INTEGER) -- in kg
- status (TEXT) -- 'active', 'injured', 'suspended', 'inactive'
- emergency_contact (TEXT)
- medical_notes (TEXT)
- joined_date (DATE)

Performance_Metrics table:
- id (TEXT PRIMARY KEY)
- player_id (TEXT)
- metric_type (TEXT) -- 'speed', 'endurance', 'strength', 'skill'
- metric_name (TEXT)
- value (DECIMAL)
- unit (TEXT)
- recorded_date (DATE)
- recorded_by (TEXT)
- notes (TEXT)
- created_at (TIMESTAMP)

Training_Sessions table:
- id (TEXT PRIMARY KEY)
- team_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- date (DATE)
- start_time (TIME)
- duration (INTEGER) -- in minutes
- location (TEXT)
- session_type (TEXT) -- 'practice', 'fitness', 'tactical', 'recovery'
- coach_id (TEXT)
- created_at (TIMESTAMP)

Training_Attendance table:
- session_id (TEXT)
- player_id (TEXT)
- attendance_status (TEXT) -- 'present', 'absent', 'excused', 'late'
- performance_rating (INTEGER) -- 1-10 scale
- notes (TEXT)
- recorded_at (TIMESTAMP)
- PRIMARY KEY (session_id, player_id)

Matches table:
- id (TEXT PRIMARY KEY)
- team_id (TEXT)
- opponent (TEXT NOT NULL)
- match_date (DATE)
- match_time (TIME)
- location (TEXT)
- match_type (TEXT) -- 'league', 'friendly', 'tournament', 'playoff'
- home_away (TEXT) -- 'home', 'away'
- team_score (INTEGER)
- opponent_score (INTEGER)
- match_status (TEXT) -- 'scheduled', 'in_progress', 'completed', 'cancelled'
- created_at (TIMESTAMP)

Match_Lineups table:
- id (TEXT PRIMARY KEY)
- match_id (TEXT)
- player_id (TEXT)
- position (TEXT)
- is_starter (BOOLEAN)
- minutes_played (INTEGER)
- substitution_time (INTEGER)
- created_at (TIMESTAMP)

Match_Statistics table:
- id (TEXT PRIMARY KEY)
- match_id (TEXT)
- player_id (TEXT)
- statistic_type (TEXT) -- 'goals', 'assists', 'saves', 'fouls'
- value (INTEGER)
- recorded_at (TIMESTAMP)

Injuries table:
- id (TEXT PRIMARY KEY)
- player_id (TEXT)
- injury_type (TEXT)
- severity (TEXT) -- 'minor', 'moderate', 'major', 'severe'
- description (TEXT)
- injury_date (DATE)
- expected_return_date (DATE)
- actual_return_date (DATE)
- status (TEXT) -- 'injured', 'recovering', 'cleared', 'chronic'
- treatment_plan (TEXT)
- reported_by (TEXT)
- created_at (TIMESTAMP)

Health_Records table:
- id (TEXT PRIMARY KEY)
- player_id (TEXT)
- checkup_type (TEXT) -- 'physical', 'fitness', 'medical', 'psychological'
- checkup_date (DATE)
- results (TEXT) -- JSON object
- recommendations (TEXT)
- clearance_status (TEXT) -- 'cleared', 'restricted', 'not_cleared'
- conducted_by (TEXT)
- created_at (TIMESTAMP)

Team_Messages table:
- id (TEXT PRIMARY KEY)
- sender_id (TEXT)
- team_id (TEXT)
- subject (TEXT)
- content (TEXT)
- message_type (TEXT) -- 'announcement', 'tactical', 'administrative'
- priority (TEXT) -- 'low', 'medium', 'high', 'urgent'
- recipients (TEXT) -- JSON array of user IDs
- sent_at (TIMESTAMP)

Equipment table:
- id (TEXT PRIMARY KEY)
- team_id (TEXT)
- equipment_type (TEXT) -- 'ball', 'uniform', 'protective', 'training'
- name (TEXT NOT NULL)
- quantity (INTEGER)
- condition (TEXT) -- 'excellent', 'good', 'fair', 'poor'
- location (TEXT)
- assigned_to (TEXT) -- player_id if assigned
- purchase_date (DATE)
- last_maintenance (DATE)
```

## Sports Management Features

- **Comprehensive player profiles** with performance history and health tracking
- **Advanced performance analytics** with trend analysis and benchmarking
- **Training optimization** with attendance tracking and performance correlation
- **Match management** with lineup planning and real-time statistics
- **Injury prevention** with health monitoring and risk assessment
- **Team communication** with role-based messaging and announcements
- **Equipment management** with inventory tracking and maintenance scheduling
- **Statistical analysis** with team and individual performance insights

## Performance Analytics Features

- **Performance trend analysis** with predictive modeling for player development
- **Comparative analytics** between players, teams, and historical data
- **Training effectiveness** measurement with outcome correlation
- **Match performance** analysis with tactical insights
- **Fitness progression** tracking with periodization support
- **Injury correlation** analysis with performance and training data
- **Team chemistry** metrics and lineup optimization
- **Seasonal progression** tracking with goal setting and achievement

## Team Coordination Features

- **Role-based access** control for coaches, players, and staff
- **Schedule coordination** with conflict detection and notifications
- **Communication channels** for different team functions and hierarchies
- **Resource allocation** with facility and equipment management
- **Match preparation** with tactical planning and player assignment
- **Recovery management** with rest periods and load monitoring
- **Team building** tools with social features and team bonding
- **Parent/guardian** communication for youth teams

## Health and Safety Features

- **Comprehensive injury tracking** with medical history and risk factors
- **Fitness monitoring** with baseline establishment and progress tracking
- **Medical clearance** management with healthcare provider integration
- **Emergency contact** management with quick access during incidents
- **Concussion protocol** tracking with return-to-play guidelines
- **Nutrition tracking** with dietary recommendations and monitoring
- **Sleep and recovery** monitoring with performance correlation
- **Mental health** support with stress and wellness tracking

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, statistics, sports analytics libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Sports performance calculation and analytics
   - Team management and coordination systems
   - Health and safety monitoring
   - Communication and notification systems
   - Performance optimization for sports data
   - Role-based access control
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all sports team management scenarios including player management, performance tracking, training coordination, match planning, and health monitoring with proper team management protocols and sports analytics.