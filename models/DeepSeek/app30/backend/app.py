from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)

# In-memory database for demonstration
recipes_db = []
users_db = []
categories = ["Breakfast", "Lunch", "Dinner", "Dessert", "Snack"]
meal_plan = {}

def calculate_nutrition(ingredients):
    """Helper function to calculate nutrition info"""
    nutrition = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0
    }
    for ingredient in ingredients:
        nutrition["calories"] += ingredient.get("calories", 0)
        nutrition["protein"] += ingredient.get("protein", 0)
        nutrition["carbs"] += ingredient.get("carbs", 0)
        nutrition["fat"] += ingredient.get("fat", 0)
    return nutrition

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes with optional filtering"""
    category = request.args.get('category')
    if category:
        filtered = [r for r in recipes_db if r['category'] == category]
        return jsonify(filtered)
    return jsonify(recipes_db)

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe by ID"""
    recipe = next((r for r in recipes_db if r['id'] == recipe_id), None)
    if not recipe:
        abort(404, description="Recipe not found")
    return jsonify(recipe)

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    """Create a new recipe"""
    data = request.json
    if not data or 'title' not in data:
        abort(400, description="Title is required")
    
    new_recipe = {
        "id": len(recipes_db) + 1,
        "title": data['title'],
        "description": data.get('description', ''),
        "category": data.get('category', 'Other'),
        "ingredients": data.get('ingredients', []),
        "instructions": data.get('instructions', ''),
        "prep_time": data.get('prep_time', 0),
        "cook_time": data.get('cook_time', 0),
        "servings": data.get('servings', 1),
        "nutrition": calculate_nutrition(data.get('ingredients', []))
    }
    recipes_db.append(new_recipe)
    return jsonify(new_recipe), 201

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """Update an existing recipe"""
    recipe = next((r for r in recipes_db if r['id'] == recipe_id), None)
    if not recipe:
        abort(404, description="Recipe not found")
    
    data = request.json
    recipe.update({
        "title": data.get('title', recipe['title']),
        "description": data.get('description', recipe['description']),
        "category": data.get('category', recipe['category']),
        "ingredients": data.get('ingredients', recipe['ingredients']),
        "instructions": data.get('instructions', recipe['instructions']),
        "prep_time": data.get('prep_time', recipe['prep_time']),
        "cook_time": data.get('cook_time', recipe['cook_time']),
        "servings": data.get('servings', recipe['servings']),
        "nutrition": calculate_nutrition(data.get('ingredients', recipe['ingredients']))
    })
    return jsonify(recipe)

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Delete a recipe"""
    global recipes_db
    recipe = next((r for r in recipes_db if r['id'] == recipe_id), None)
    if not recipe:
        abort(404, description="Recipe not found")
    recipes_db = [r for r in recipes_db if r['id'] != recipe_id]
    return jsonify({"message": "Recipe deleted"})

@app.route('/api/meal-plan', methods=['GET'])
def get_meal_plan():
    """Get the meal plan for the week"""
    return jsonify(meal_plan)

@app.route('/api/meal-plan', methods=['POST'])
def add_to_meal_plan():
    """Add a recipe to the meal plan"""
    data = request.json
    if not data or 'recipe_id' not in data or 'date' not in data or 'meal_type' not in data:
        abort(400, description="recipe_id, date and meal_type are required")
    
    recipe = next((r for r in recipes_db if r['id'] == data['recipe_id']), None)
    if not recipe:
        abort(404, description="Recipe not found")
    
    meal_plan[data['date']] = meal_plan.get(data['date'], {})
    meal_plan[data['date']][data['meal_type']] = recipe['id']
    return jsonify(meal_plan)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all recipe categories"""
    return jsonify(categories)

@app.route('/api/timer/start', methods=['POST'])
def start_timer():
    """Start a cooking timer"""
    data = request.json
    if not data or 'duration' not in data:
        abort(400, description="Duration is required")
    
    end_time = datetime.now() + timedelta(seconds=data['duration'])
    return jsonify({
        "message": "Timer started",
        "ends_at": end_time.isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5219')))
