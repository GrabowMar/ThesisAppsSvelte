# Backend Generation Prompt - Flask Environmental Impact Tracking Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/carbon`, `/api/challenges`, `/api/consumption`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Environmental Sustainability Tracking System Backend**  
A comprehensive Flask backend for environmental impact application, featuring carbon footprint calculation, sustainability challenge management, resource consumption monitoring, eco-friendly recommendations, community impact analysis, and waste reduction tracking with scientific accuracy and gamification elements.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Comprehensive carbon footprint calculation and tracking
- Sustainability challenge creation and management
- Resource consumption monitoring (water, energy, waste)
- Evidence-based eco-friendly tips and recommendations
- Progress visualization and environmental impact analytics
- Community comparison and social impact features
- Recycling and waste reduction tracking systems
- User authentication and environmental profile management
- Achievement and gamification system for sustainability
- Environmental data integration and API connections
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
import math
from decimal import Decimal

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Carbon Calculation Logic
# 5. Sustainability Algorithms
# 6. Environmental Data Processing
# 7. API Routes:
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - POST /api/carbon/track (record carbon activity)
#    - GET /api/carbon/footprint (get carbon footprint data)
#    - GET /api/carbon/breakdown (get detailed carbon analysis)
#    - POST /api/consumption/track (record resource consumption)
#    - GET /api/consumption/history (get consumption history)
#    - GET /api/consumption/analytics (get consumption analytics)
#    - GET /api/challenges (get sustainability challenges)
#    - POST /api/challenges (create challenge)
#    - POST /api/challenges/<id>/join (join challenge)
#    - PUT /api/challenges/<id>/progress (update challenge progress)
#    - GET /api/waste/track (track waste and recycling)
#    - POST /api/waste/log (log waste activity)
#    - GET /api/waste/analytics (get waste reduction analytics)
#    - GET /api/tips (get personalized eco-tips)
#    - POST /api/tips/rate (rate tip effectiveness)
#    - GET /api/community/leaderboard (get community rankings)
#    - GET /api/community/impact (get collective impact data)
#    - GET /api/achievements (get user achievements)
#    - GET /api/reports/monthly (get monthly environmental report)
#    - GET /api/reports/yearly (get yearly impact summary)
#    - GET /api/calculator/transport (calculate transportation emissions)
#    - GET /api/calculator/energy (calculate energy emissions)
#    - GET /api/calculator/diet (calculate food-related emissions)
#    - POST /api/goals/set (set environmental goals)
#    - GET /api/goals/progress (get goal progress)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, location, household_size
   - Validate input and create user account
   - Hash password securely
   - Initialize environmental profile and baseline metrics
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and environmental status

3. **POST /api/auth/logout**
   - Clear user session
   - Save pending environmental data
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include environmental preferences and settings

### Carbon Footprint Tracking Routes

5. **POST /api/carbon/track**
   - Record carbon-generating activity
   - Accept: activity_type, amount, unit, date, details
   - Calculate CO2 equivalent emissions
   - Return carbon impact and running total

6. **GET /api/carbon/footprint**
   - Return user's carbon footprint data
   - Include daily, weekly, monthly, yearly totals
   - Support date range filtering and comparisons

7. **GET /api/carbon/breakdown**
   - Return detailed carbon footprint analysis
   - Break down by categories (transport, energy, food, waste)
   - Include improvement recommendations

### Resource Consumption Routes

8. **POST /api/consumption/track**
   - Record resource consumption activity
   - Accept: resource_type, amount, unit, date, efficiency_rating
   - Calculate environmental impact
   - Return consumption summary

9. **GET /api/consumption/history**
   - Return consumption history with trends
   - Include water, energy, waste consumption
   - Support filtering by resource type and date

10. **GET /api/consumption/analytics**
    - Return consumption analytics and insights
    - Include efficiency scores and benchmarks
    - Provide reduction recommendations

### Sustainability Challenge Routes

11. **GET /api/challenges**
    - Return available sustainability challenges
    - Include challenge details, duration, difficulty
    - Show user participation status

12. **POST /api/challenges**
    - Create new sustainability challenge
    - Accept: title, description, goals, duration, category
    - Return created challenge

13. **POST /api/challenges/<id>/join**
    - Join sustainability challenge
    - Initialize challenge tracking
    - Return participation confirmation

14. **PUT /api/challenges/<id>/progress**
    - Update challenge progress
    - Accept: progress_data, milestone_reached
    - Calculate completion percentage
    - Return updated progress

### Waste and Recycling Routes

15. **GET /api/waste/track**
    - Return waste tracking data
    - Include recycling rates and waste reduction
    - Show waste categories and disposal methods

16. **POST /api/waste/log**
    - Log waste and recycling activity
    - Accept: waste_type, amount, disposal_method, recyclable
    - Calculate environmental impact
    - Return waste summary

17. **GET /api/waste/analytics**
    - Return waste reduction analytics
    - Include recycling efficiency and improvements
    - Provide waste reduction recommendations

### Eco-Tips and Recommendations Routes

18. **GET /api/tips**
    - Return personalized eco-friendly tips
    - Base recommendations on user's environmental profile
    - Include evidence-based sustainability practices

19. **POST /api/tips/rate**
    - Rate effectiveness of eco-tip
    - Accept: tip_id, effectiveness_rating, implemented
    - Update tip recommendation algorithm
    - Return rating confirmation

### Community and Social Impact Routes

20. **GET /api/community/leaderboard**
    - Return community environmental rankings
    - Include top performers and achievements
    - Show user's position and progress

21. **GET /api/community/impact**
    - Return collective community impact data
    - Include total carbon saved, challenges completed
    - Show community environmental goals

22. **GET /api/achievements**
    - Return user's environmental achievements
    - Include badges, milestones, and recognition
    - Show progress toward next achievements

### Reporting and Analysis Routes

23. **GET /api/reports/monthly**
    - Return monthly environmental impact report
    - Include carbon footprint, consumption, achievements
    - Provide month-over-month comparisons

24. **GET /api/reports/yearly**
    - Return yearly environmental impact summary
    - Include annual totals, trends, and improvements
    - Show long-term environmental progress

### Environmental Calculator Routes

25. **GET /api/calculator/transport**
    - Calculate transportation carbon emissions
    - Accept: transport_mode, distance, frequency
    - Return CO2 emissions and alternatives

26. **GET /api/calculator/energy**
    - Calculate home energy carbon emissions
    - Accept: energy_type, consumption, efficiency
    - Return emissions and efficiency recommendations

27. **GET /api/calculator/diet**
    - Calculate food-related carbon emissions
    - Accept: diet_type, meal_frequency, food_waste
    - Return dietary carbon impact and alternatives

### Goal Setting Routes

28. **POST /api/goals/set**
    - Set environmental improvement goals
    - Accept: goal_type, target_value, target_date
    - Return created goal

29. **GET /api/goals/progress**
    - Return progress toward environmental goals
    - Include completion percentage and timeline
    - Show goal achievement predictions

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- location (TEXT)
- household_size (INTEGER)
- created_at (TIMESTAMP)
- total_carbon_saved (DECIMAL DEFAULT 0)
- sustainability_score (INTEGER DEFAULT 0)
- current_streak (INTEGER DEFAULT 0)

Carbon_Activities table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- activity_type (TEXT) -- 'transport', 'energy', 'food', 'waste'
- activity_name (TEXT)
- amount (DECIMAL)
- unit (TEXT)
- co2_emissions (DECIMAL)
- date (DATE)
- notes (TEXT)
- created_at (TIMESTAMP)

Resource_Consumption table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- resource_type (TEXT) -- 'water', 'electricity', 'gas', 'waste'
- amount (DECIMAL)
- unit (TEXT)
- environmental_impact (DECIMAL)
- efficiency_score (INTEGER)
- date (DATE)
- created_at (TIMESTAMP)

Sustainability_Challenges table:
- id (TEXT PRIMARY KEY)
- creator_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- category (TEXT) -- 'transport', 'energy', 'waste', 'diet'
- difficulty_level (INTEGER)
- duration_days (INTEGER)
- target_metric (TEXT)
- target_value (DECIMAL)
- start_date (DATE)
- end_date (DATE)
- participant_count (INTEGER DEFAULT 0)
- is_active (BOOLEAN DEFAULT TRUE)

Challenge_Participants table:
- challenge_id (TEXT)
- user_id (TEXT)
- joined_at (TIMESTAMP)
- current_progress (DECIMAL DEFAULT 0)
- is_completed (BOOLEAN DEFAULT FALSE)
- completed_at (TIMESTAMP)
- PRIMARY KEY (challenge_id, user_id)

Waste_Tracking table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- waste_type (TEXT) -- 'plastic', 'paper', 'organic', 'electronic'
- amount (DECIMAL)
- unit (TEXT) -- 'kg', 'items', 'bags'
- disposal_method (TEXT) -- 'recycle', 'compost', 'landfill', 'reuse'
- environmental_impact (DECIMAL)
- date (DATE)
- created_at (TIMESTAMP)

Eco_Tips table:
- id (TEXT PRIMARY KEY)
- title (TEXT NOT NULL)
- description (TEXT)
- category (TEXT)
- impact_level (TEXT) -- 'low', 'medium', 'high'
- difficulty (TEXT) -- 'easy', 'medium', 'hard'
- estimated_savings (DECIMAL) -- CO2 saved per month
- evidence_source (TEXT)
- usage_count (INTEGER DEFAULT 0)

User_Tip_Ratings table:
- user_id (TEXT)
- tip_id (TEXT)
- effectiveness_rating (INTEGER) -- 1-5 scale
- implemented (BOOLEAN)
- rating_date (TIMESTAMP)
- notes (TEXT)
- PRIMARY KEY (user_id, tip_id)

Environmental_Goals table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- goal_type (TEXT) -- 'carbon_reduction', 'energy_efficiency', 'waste_reduction'
- title (TEXT NOT NULL)
- target_value (DECIMAL)
- current_progress (DECIMAL DEFAULT 0)
- target_date (DATE)
- is_achieved (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)

Achievements table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- category (TEXT)
- criteria (TEXT) -- JSON object
- badge_icon (TEXT)
- co2_threshold (DECIMAL)
- rarity (TEXT) -- 'common', 'rare', 'epic', 'legendary'

User_Achievements table:
- user_id (TEXT)
- achievement_id (TEXT)
- earned_at (TIMESTAMP)
- progress_data (TEXT) -- JSON object
- PRIMARY KEY (user_id, achievement_id)

Environmental_Reports table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- report_type (TEXT) -- 'monthly', 'yearly'
- period_start (DATE)
- period_end (DATE)
- total_carbon_footprint (DECIMAL)
- carbon_saved (DECIMAL)
- sustainability_score (INTEGER)
- report_data (TEXT) -- JSON object
- generated_at (TIMESTAMP)
```

## Environmental Calculation Features

- **Scientific carbon footprint** calculations based on EPA and IPCC standards
- **Regional emission factors** for accurate location-based calculations
- **Activity-specific algorithms** for transport, energy, food, and waste
- **Lifecycle assessment** integration for comprehensive impact analysis
- **Carbon offset calculations** and verification systems
- **Renewable energy** impact calculations and credits
- **Seasonal adjustments** for heating, cooling, and transportation patterns
- **Efficiency scoring** algorithms for resource consumption optimization

## Sustainability Challenge Features

- **Evidence-based challenges** with scientific backing and measurable outcomes
- **Difficulty progression** system from beginner to advanced sustainability
- **Community challenges** for collective environmental impact
- **Seasonal challenges** aligned with environmental awareness campaigns
- **Custom challenge** creation with goal setting and tracking
- **Challenge categories** covering all aspects of environmental impact
- **Progress tracking** with milestone celebrations and rewards
- **Challenge leaderboards** with friendly competition and recognition

## Environmental Analytics Features

- **Trend analysis** for carbon footprint and resource consumption patterns
- **Benchmarking** against regional and global sustainability averages
- **Predictive modeling** for future environmental impact projections
- **Impact visualization** with charts, graphs, and infographics
- **Comparative analysis** between different lifestyle choices
- **Cost-benefit analysis** for sustainability investments and changes
- **Environmental ROI** calculations for green initiatives
- **Progress forecasting** toward sustainability goals and targets

## Community and Gamification Features

- **Leaderboards** with privacy-respecting rankings and achievements
- **Team challenges** for households, neighborhoods, and organizations
- **Social sharing** of achievements and environmental milestones
- **Mentorship programs** pairing experienced with new users
- **Community goals** with collective impact tracking
- **Recognition systems** with badges, points, and environmental impact scores
- **Educational content** with tips, tutorials, and sustainability guides
- **Success stories** sharing and inspiration from community members

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, environmental calculation, data analysis libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Environmental calculation accuracy and validation
   - Sustainability challenge management
   - Community feature implementation
   - Progress tracking and analytics
   - Performance optimization for environmental data
   - Scientific accuracy in carbon calculations
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all environmental tracking scenarios including carbon footprint calculation, sustainability challenges, resource monitoring, and community engagement with proper scientific accuracy and environmental best practices.