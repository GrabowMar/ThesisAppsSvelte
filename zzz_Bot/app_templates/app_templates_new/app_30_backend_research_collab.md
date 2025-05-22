# Backend Generation Prompt - Flask Recipe Management Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/recipes`, `/api/ingredients`, `/api/meal-plans`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Recipe Management System Backend**  
A comprehensive Flask backend for recipe management application, featuring recipe creation, ingredient tracking, meal planning, nutrition calculation, categorization, and cooking assistance with sharing and collaboration capabilities.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete recipe creation and editing system
- Comprehensive ingredient tracking and management
- Meal planning with calendar integration
- Recipe categorization and tagging system
- Nutrition information calculation and tracking
- Cooking timer and step-by-step guidance
- Recipe sharing and collaboration features
- Shopping list generation from meal plans
- Recipe scaling and conversion tools
- User authentication and profile management
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
from decimal import Decimal
import re

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Recipe Logic
# 5. Nutrition Calculation
# 6. Meal Planning Logic
# 7. API Routes:
#    - GET /api/recipes (list recipes with filtering)
#    - GET /api/recipes/<id> (get specific recipe)
#    - POST /api/recipes (create new recipe)
#    - PUT /api/recipes/<id> (update recipe)
#    - DELETE /api/recipes/<id> (delete recipe)
#    - GET /api/recipes/<id>/nutrition (get nutrition info)
#    - POST /api/recipes/<id>/scale (scale recipe servings)
#    - GET /api/ingredients (list ingredients)
#    - POST /api/ingredients (add ingredient)
#    - PUT /api/ingredients/<id> (update ingredient)
#    - DELETE /api/ingredients/<id> (delete ingredient)
#    - GET /api/categories (list categories)
#    - POST /api/categories (create category)
#    - PUT /api/categories/<id> (update category)
#    - DELETE /api/categories/<id> (delete category)
#    - GET /api/meal-plans (get meal plans)
#    - POST /api/meal-plans (create meal plan)
#    - PUT /api/meal-plans/<id> (update meal plan)
#    - DELETE /api/meal-plans/<id> (delete meal plan)
#    - GET /api/meal-plans/<id>/shopping-list (generate shopping list)
#    - GET /api/search (search recipes)
#    - POST /api/recipes/<id>/favorite (favorite/unfavorite)
#    - GET /api/recipes/favorites (get favorite recipes)
#    - POST /api/recipes/<id>/share (share recipe)
#    - GET /api/timers (get cooking timers)
#    - POST /api/timers (create timer)
#    - PUT /api/timers/<id> (update timer)
#    - DELETE /api/timers/<id> (delete timer)
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
   - Accept: username, email, password, full_name
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
   - Include user stats (recipes created, meal plans, favorites)

### Recipe Management Routes

5. **GET /api/recipes**
   - Return paginated list of recipes
   - Support filtering by category, cuisine, difficulty, time
   - Support sorting by date, rating, popularity, time
   - Include recipe metadata and thumbnails

6. **GET /api/recipes/<id>**
   - Return specific recipe with full details
   - Include ingredients, instructions, nutrition, ratings
   - Track view count and user interactions

7. **POST /api/recipes**
   - Create new recipe
   - Accept: title, description, ingredients, instructions, category, servings, cook_time
   - Validate recipe structure
   - Calculate nutrition information
   - Return created recipe

8. **PUT /api/recipes/<id>**
   - Update existing recipe
   - Require authentication and ownership
   - Recalculate nutrition if ingredients changed
   - Return updated recipe

9. **DELETE /api/recipes/<id>**
   - Delete recipe
   - Require authentication and ownership
   - Handle meal plan dependencies
   - Return confirmation

10. **GET /api/recipes/<id>/nutrition**
    - Return detailed nutrition information
    - Include per-serving and total nutrition
    - Show macro and micronutrient breakdown

11. **POST /api/recipes/<id>/scale**
    - Scale recipe for different serving sizes
    - Accept: target_servings
    - Calculate adjusted ingredient quantities
    - Return scaled recipe

### Ingredient Management Routes

12. **GET /api/ingredients**
    - Return list of ingredients
    - Include nutrition data and common measurements
    - Support search and filtering

13. **POST /api/ingredients**
    - Add new ingredient to database
    - Accept: name, nutrition_data, common_units
    - Return created ingredient

14. **PUT /api/ingredients/<id>**
    - Update ingredient information
    - Accept: name, nutrition_data, common_units
    - Return updated ingredient

15. **DELETE /api/ingredients/<id>**
    - Delete ingredient
    - Check for recipe dependencies
    - Return confirmation

### Category and Organization Routes

16. **GET /api/categories**
    - Return list of recipe categories
    - Include recipe counts and descriptions

17. **POST /api/categories**
    - Create new category
    - Accept: name, description, parent_id
    - Return created category

18. **PUT /api/categories/<id>**
    - Update category details
    - Return updated category

19. **DELETE /api/categories/<id>**
    - Delete category
    - Handle recipe reassignment
    - Return confirmation

### Meal Planning Routes

20. **GET /api/meal-plans**
    - Return user's meal plans
    - Support date range filtering
    - Include recipe details and nutrition summaries

21. **POST /api/meal-plans**
    - Create new meal plan
    - Accept: name, start_date, end_date, meals
    - Validate recipe assignments
    - Return created meal plan

22. **PUT /api/meal-plans/<id>**
    - Update meal plan
    - Accept: meals, dates, recipes
    - Recalculate nutrition totals
    - Return updated meal plan

23. **DELETE /api/meal-plans/<id>**
    - Delete meal plan
    - Return confirmation

24. **GET /api/meal-plans/<id>/shopping-list**
    - Generate shopping list from meal plan
    - Aggregate ingredients across recipes
    - Group by grocery store sections
    - Return organized shopping list

### Search and Discovery Routes

25. **GET /api/search**
    - Search recipes by name, ingredients, tags
    - Accept: query, filters (cuisine, time, difficulty)
    - Support advanced search with operators
    - Return ranked search results

26. **POST /api/recipes/<id>/favorite**
    - Add/remove recipe from favorites
    - Require authentication
    - Toggle favorite status
    - Return updated status

27. **GET /api/recipes/favorites**
    - Return user's favorite recipes
    - Include pagination and sorting
    - Show favorite date

28. **POST /api/recipes/<id>/share**
    - Share recipe with other users
    - Accept: user_ids, permissions
    - Create sharing record
    - Return sharing confirmation

### Cooking Assistant Routes

29. **GET /api/timers**
    - Return active cooking timers for user
    - Include timer details and remaining time

30. **POST /api/timers**
    - Create new cooking timer
    - Accept: name, duration, recipe_id, step
    - Return created timer

31. **PUT /api/timers/<id>**
    - Update timer (pause, resume, modify)
    - Return updated timer

32. **DELETE /api/timers/<id>**
    - Delete timer
    - Return confirmation

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- full_name (TEXT)
- created_at (TIMESTAMP)
- recipes_created (INTEGER DEFAULT 0)
- favorite_count (INTEGER DEFAULT 0)
- meal_plans_created (INTEGER DEFAULT 0)

Recipes table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- category_id (INTEGER)
- cuisine (TEXT)
- difficulty (TEXT) -- 'easy', 'medium', 'hard'
- prep_time (INTEGER) -- minutes
- cook_time (INTEGER) -- minutes
- total_time (INTEGER) -- minutes
- servings (INTEGER)
- instructions (TEXT) -- JSON array
- image_url (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- view_count (INTEGER DEFAULT 0)
- favorite_count (INTEGER DEFAULT 0)

Ingredients table:
- id (TEXT PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- category (TEXT) -- 'protein', 'vegetable', 'grain', etc.
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
- ingredient_id (TEXT)
- quantity (DECIMAL)
- unit (TEXT)
- preparation (TEXT) -- 'diced', 'chopped', 'minced', etc.
- optional (BOOLEAN DEFAULT FALSE)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- parent_id (INTEGER)
- recipe_count (INTEGER DEFAULT 0)

Meal_Plans table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT NOT NULL)
- start_date (DATE)
- end_date (DATE)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Meal_Plan_Items table:
- id (TEXT PRIMARY KEY)
- meal_plan_id (TEXT)
- recipe_id (TEXT)
- meal_date (DATE)
- meal_type (TEXT) -- 'breakfast', 'lunch', 'dinner', 'snack'
- servings (INTEGER DEFAULT 1)

Recipe_Favorites table:
- user_id (TEXT)
- recipe_id (TEXT)
- created_at (TIMESTAMP)

Cooking_Timers table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- recipe_id (TEXT)
- name (TEXT NOT NULL)
- duration (INTEGER) -- seconds
- started_at (TIMESTAMP)
- paused_at (TIMESTAMP)
- completed_at (TIMESTAMP)

Recipe_Shares table:
- id (TEXT PRIMARY KEY)
- recipe_id (TEXT)
- shared_by (TEXT)
- shared_with (TEXT)
- permissions (TEXT) -- 'view', 'edit'
- shared_at (TIMESTAMP)
```

## Recipe Management Features

- **Comprehensive recipe storage** with detailed metadata
- **Ingredient management** with nutrition database
- **Recipe scaling** with automatic quantity adjustments
- **Nutrition calculation** based on ingredients and servings
- **Recipe categorization** with hierarchical organization
- **Search and filtering** by multiple criteria
- **Recipe sharing** with permission controls
- **Favorite recipes** management and organization

## Meal Planning Features

- **Calendar-based meal planning** with drag-and-drop interface
- **Automatic shopping list** generation from meal plans
- **Nutrition tracking** across meal plans
- **Recipe suggestions** based on dietary preferences
- **Meal prep scheduling** and timing
- **Leftover management** and recipe suggestions
- **Dietary restriction** filtering and substitutions

## Nutrition and Health Features

- **Detailed nutrition calculation** for recipes and meal plans
- **Macro and micronutrient** tracking
- **Dietary goal** setting and progress tracking
- **Allergen identification** and warnings
- **Ingredient substitution** suggestions
- **Calorie counting** and meal balance analysis
- **Nutritional analysis** reports and insights

## Cooking Assistant Features

- **Step-by-step cooking** guidance with timers
- **Multiple timer** management for complex recipes
- **Cooking tips** and technique suggestions
- **Temperature guidance** for cooking and baking
- **Recipe difficulty** assessment and skill building
- **Cooking time estimation** based on experience
- **Kitchen equipment** recommendations

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, nutrition calculation libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation and sanitization
   - Recipe data validation and nutrition calculation
   - Meal planning optimization
   - Search optimization with indexing
   - Performance optimization for large recipe collections
   - User preference and recommendation system
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all recipe management scenarios including recipe creation, ingredient tracking, meal planning, nutrition calculation, and cooking assistance with proper validation and optimization.