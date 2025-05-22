# Backend Generation Prompt - Flask Recipe Management Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/recipes`, `/api/ingredients`, `/api/meals`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Recipe Management System Backend**  
A comprehensive Flask backend for recipe management application, featuring recipe creation, ingredient tracking, meal planning, nutrition calculation, cooking timers, and collaborative recipe sharing with dietary preferences and smart recommendations.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete recipe creation, editing, and management system
- Comprehensive ingredient database and tracking
- Intelligent meal planning with dietary restrictions
- Recipe categorization and tagging system
- Nutrition information calculation and analysis
- Cooking timer management and notifications
- User authentication and recipe sharing
- Search and filtering with advanced criteria
- Recipe rating and review system
- Shopping list generation from meal plans
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
from fractions import Fraction
import re

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Nutrition Calculations
# 5. Recipe Processing
# 6. Meal Planning Logic
# 7. API Routes:
#    - GET /api/recipes (list recipes)
#    - GET /api/recipes/<id> (get recipe details)
#    - POST /api/recipes (create recipe)
#    - PUT /api/recipes/<id> (update recipe)
#    - DELETE /api/recipes/<id> (delete recipe)
#    - GET /api/ingredients (get ingredients database)
#    - POST /api/ingredients (add custom ingredient)
#    - PUT /api/ingredients/<id> (update ingredient)
#    - GET /api/categories (get recipe categories)
#    - POST /api/categories (create category)
#    - GET /api/meal-plans (get meal plans)
#    - POST /api/meal-plans (create meal plan)
#    - PUT /api/meal-plans/<id> (update meal plan)
#    - DELETE /api/meal-plans/<id> (delete meal plan)
#    - GET /api/nutrition/<recipe_id> (get nutrition info)
#    - POST /api/timers (create cooking timer)
#    - GET /api/timers (get active timers)
#    - PUT /api/timers/<id> (update timer)
#    - DELETE /api/timers/<id> (delete timer)
#    - GET /api/search (search recipes)
#    - GET /api/shopping-list (generate shopping list)
#    - POST /api/reviews (add recipe review)
#    - GET /api/reviews/<recipe_id> (get recipe reviews)
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
   - Accept: username, email, password, dietary_preferences, cooking_skill
   - Validate input and create user account
   - Initialize user preferences and dietary restrictions
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and preferences

3. **POST /api/auth/logout**
   - Clear user session
   - Stop any active cooking timers
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include dietary preferences and cooking statistics

### Recipe Management Routes

5. **GET /api/recipes**
   - Return list of recipes
   - Support filtering by category, dietary restrictions, cooking time
   - Include recipe metadata and ratings
   - Support pagination and sorting

6. **GET /api/recipes/<id>**
   - Return specific recipe with full details
   - Include ingredients, instructions, nutrition info
   - Show user ratings and reviews
   - Track recipe view counts

7. **POST /api/recipes**
   - Create new recipe
   - Accept: title, description, ingredients, instructions, prep_time, cook_time, servings, category
   - Calculate nutrition information automatically
   - Return created recipe with generated data

8. **PUT /api/recipes/<id>**
   - Update existing recipe
   - Accept: title, description, ingredients, instructions, timing, servings
   - Recalculate nutrition information
   - Require recipe ownership or admin permissions

9. **DELETE /api/recipes/<id>**
   - Delete recipe
   - Remove from meal plans and user favorites
   - Require appropriate permissions
   - Return confirmation

### Ingredient Management Routes

10. **GET /api/ingredients**
    - Return ingredients database
    - Include nutrition data per serving
    - Support search and filtering by category
    - Show user-added custom ingredients

11. **POST /api/ingredients**
    - Add custom ingredient to database
    - Accept: name, category, nutrition_per_100g, common_units
    - Validate nutrition data
    - Return created ingredient

12. **PUT /api/ingredients/<id>**
    - Update ingredient information
    - Accept: name, category, nutrition_data, units
    - Require admin permissions for base ingredients
    - Return updated ingredient

### Meal Planning Routes

13. **GET /api/meal-plans**
    - Return user's meal plans
    - Accept: date_range, meal_type
    - Include planned recipes and nutrition summaries
    - Support weekly and monthly planning

14. **POST /api/meal-plans**
    - Create meal plan
    - Accept: date, meal_type, recipe_id, servings, notes
    - Validate recipe availability and dietary restrictions
    - Return created meal plan

15. **PUT /api/meal-plans/<id>**
    - Update meal plan entry
    - Accept: recipe_id, servings, notes, date
    - Recalculate nutrition totals
    - Return updated meal plan

16. **DELETE /api/meal-plans/<id>**
    - Remove meal from plan
    - Update nutrition calculations
    - Return confirmation

### Nutrition and Analysis Routes

17. **GET /api/nutrition/<recipe_id>**
    - Calculate and return detailed nutrition information
    - Include macronutrients, vitamins, minerals
    - Show nutrition per serving and per 100g
    - Calculate daily value percentages

18. **GET /api/categories**
    - Return recipe categories and cuisine types
    - Include category descriptions and recipe counts
    - Support hierarchical categories

19. **POST /api/categories**
    - Create new recipe category
    - Accept: name, description, parent_category
    - Return created category

### Timer Management Routes

20. **POST /api/timers**
    - Create cooking timer
    - Accept: name, duration, recipe_id, timer_type
    - Store timer with user session
    - Return timer ID and start time

21. **GET /api/timers**
    - Return active timers for user
    - Include remaining time and timer details
    - Support multiple concurrent timers

22. **PUT /api/timers/<id>**
    - Update timer (pause, resume, extend)
    - Accept: action, additional_time
    - Return updated timer status

23. **DELETE /api/timers/<id>**
    - Stop and remove timer
    - Return confirmation

### Search and Discovery Routes

24. **GET /api/search**
    - Search recipes by ingredients, name, category
    - Accept: query, dietary_filters, max_cook_time, difficulty
    - Return ranked search results
    - Support ingredient-based recipe suggestions

25. **GET /api/shopping-list**
    - Generate shopping list from meal plans
    - Accept: date_range, consolidate_ingredients
    - Group ingredients by category
    - Calculate total quantities needed

26. **POST /api/reviews**
    - Add recipe review and rating
    - Accept: recipe_id, rating, comment, difficulty_rating
    - Require authentication
    - Return created review

27. **GET /api/reviews/<recipe_id>**
    - Return reviews for specific recipe
    - Include ratings and comments
    - Calculate average ratings

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- dietary_preferences (TEXT) -- JSON array
- allergies (TEXT) -- JSON array
- cooking_skill (TEXT DEFAULT 'beginner')
- created_at (TIMESTAMP)
- recipe_count (INTEGER DEFAULT 0)

Recipes table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- prep_time (INTEGER) -- minutes
- cook_time (INTEGER) -- minutes
- total_time (INTEGER) -- minutes
- servings (INTEGER)
- difficulty (TEXT) -- 'easy', 'medium', 'hard'
- category_id (INTEGER)
- instructions (TEXT) -- JSON array
- image_url (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- view_count (INTEGER DEFAULT 0)
- average_rating (DECIMAL DEFAULT 0)
- review_count (INTEGER DEFAULT 0)

Ingredients table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- category (TEXT)
- calories_per_100g (DECIMAL)
- protein_per_100g (DECIMAL)
- carbs_per_100g (DECIMAL)
- fat_per_100g (DECIMAL)
- fiber_per_100g (DECIMAL)
- sugar_per_100g (DECIMAL)
- sodium_per_100g (DECIMAL)
- common_units (TEXT) -- JSON array

Recipe_Ingredients table:
- id (TEXT PRIMARY KEY)
- recipe_id (TEXT)
- ingredient_id (INTEGER)
- quantity (DECIMAL)
- unit (TEXT)
- notes (TEXT)
- order_index (INTEGER)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- parent_id (INTEGER)
- recipe_count (INTEGER DEFAULT 0)

Meal_Plans table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- date (DATE)
- meal_type (TEXT) -- 'breakfast', 'lunch', 'dinner', 'snack'
- recipe_id (TEXT)
- servings (DECIMAL)
- notes (TEXT)
- created_at (TIMESTAMP)

Reviews table:
- id (TEXT PRIMARY KEY)
- recipe_id (TEXT)
- user_id (TEXT)
- rating (INTEGER) -- 1-5 stars
- comment (TEXT)
- difficulty_rating (INTEGER) -- 1-5
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Cooking_Timers table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- recipe_id (TEXT)
- name (TEXT NOT NULL)
- duration (INTEGER) -- seconds
- started_at (TIMESTAMP)
- is_active (BOOLEAN DEFAULT TRUE)
- timer_type (TEXT) -- 'prep', 'cook', 'rest', 'custom'

User_Favorites table:
- user_id (TEXT)
- recipe_id (TEXT)
- added_at (TIMESTAMP)
```

## Recipe Processing Features

- **Automatic nutrition calculation** from ingredients
- **Serving size scaling** with proportional adjustments
- **Recipe difficulty assessment** based on techniques and time
- **Ingredient substitution** suggestions for dietary restrictions
- **Cost estimation** based on average ingredient prices
- **Recipe validation** for completeness and accuracy
- **Duplicate recipe detection** and merging
- **Recipe versioning** and change tracking

## Nutrition Analysis Features

- **Comprehensive macro/micronutrient** calculation
- **Dietary restriction compliance** checking
- **Allergen identification** and warnings
- **Daily value percentages** calculation
- **Nutritional goal tracking** and recommendations
- **Custom nutrition targets** for different diets
- **Ingredient nutrition** database with verified data
- **Portion size** impact on nutrition values

## Meal Planning Features

- **Smart meal recommendations** based on preferences
- **Balanced nutrition planning** across meals
- **Shopping list optimization** with quantity consolidation
- **Leftover management** and recipe suggestions
- **Seasonal ingredient** recommendations
- **Budget-conscious** meal planning options
- **Meal prep** batch cooking suggestions
- **Dietary goal** alignment and tracking

## Timer and Cooking Features

- **Multiple concurrent timers** for complex recipes
- **Step-by-step cooking** guidance with timers
- **Temperature reminders** and doneness checks
- **Timer notifications** with audio and visual alerts
- **Recipe timing** optimization and suggestions
- **Cooking technique** explanations and tips
- **Equipment recommendations** based on recipes
- **Scaling cooking times** for different quantities

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, nutrition calculation libraries, time handling

3. **Production Ready Features**
   - Comprehensive error handling
   - Recipe and ingredient validation
   - Nutrition calculation accuracy
   - Meal planning optimization
   - Timer management and notifications
   - Search indexing and performance
   - User preference handling
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all recipe management scenarios including recipe creation, meal planning, nutrition tracking, cooking timers, and collaborative features with proper validation and dietary consideration.