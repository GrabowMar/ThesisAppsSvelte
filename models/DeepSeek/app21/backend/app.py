from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# In-memory database (replace with real database in production)
recipes_db = []
categories_db = ['Breakfast', 'Lunch', 'Dinner', 'Snack', 'Dessert']
active_timers = {}

# Utility functions
def calculate_nutrition(ingredients):
    calories = 0
    protein = 0
    carbs = 0
    fat = 0
    
    for ing in ingredients:
        calories += ing.get('calories', 0)
        protein += ing.get('protein', 0)
        carbs += ing.get('carbs', 0)
        fat += ing.get('fat', 0)
    
    return {
        'calories': calories,
        'protein': protein,
        'carbs': carbs,
        'fat': fat
    }

# API Routes
@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    return jsonify({'recipes': recipes_db})

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = next((r for r in recipes_db if r['id'] == recipe_id), None)
    if not recipe:
        abort(404)
    return jsonify(recipe)

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    if not request.json or 'title' not in request.json:
        abort(400)
    
    new_recipe = {
        'id': len(recipes_db) + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ''),
        'ingredients': request.json.get('ingredients', []),
        'instructions': request.json.get('instructions', []),
        'category': request.json.get('category', 'Uncategorized'),
        'prep_time': request.json.get('prep_time', 0),
        'cook_time': request.json.get('cook_time', 0),
        'servings': request.json.get('servings', 1),
        'nutrition': calculate_nutrition(request.json.get('ingredients', [])),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    recipes_db.append(new_recipe)
    return jsonify(new_recipe), 201

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    recipe = next((r for r in recipes_db if r['id'] == recipe_id), None)
    if not recipe:
        abort(404)
    
    if not request.json:
        abort(400)
    
    recipe['title'] = request.json.get('title', recipe['title'])
    recipe['description'] = request.json.get('description', recipe['description'])
    recipe['ingredients'] = request.json.get('ingredients', recipe['ingredients'])
    recipe['instructions'] = request.json.get('instructions', recipe['instructions'])
    recipe['category'] = request.json.get('category', recipe['category'])
    recipe['prep_time'] = request.json.get('prep_time', recipe['prep_time'])
    recipe['cook_time'] = request.json.get('cook_time', recipe['cook_time'])
    recipe['servings'] = request.json.get('servings', recipe['servings'])
    recipe['nutrition'] = calculate_nutrition(recipe['ingredients'])
    recipe['updated_at'] = datetime.now().isoformat()
    
    return jsonify(recipe)

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    global recipes_db
    recipe = next((r for r in recipes_db if r['id'] == recipe_id), None)
    if not recipe:
        abort(404)
    
    recipes_db = [r for r in recipes_db if r['id'] != recipe_id]
    return jsonify({'result': True})

@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify({'categories': categories_db})

@app.route('/api/timer/start', methods=['POST'])
def start_timer():
    if not request.json or 'duration' not in request.json or 'recipe_id' not in request.json:
        abort(400)
    
    timer_id = len(active_timers) + 1
    active_timers[timer_id] = {
        'recipe_id': request.json['recipe_id'],
        'duration': request.json['duration'],
        'start_time': datetime.now().isoformat(),
        'remaining': request.json['duration'],
        'active': True
    }
    
    return jsonify({'timer_id': timer_id, 'message': 'Timer started'})

@app.route('/api/timer/<int:timer_id>', methods=['GET'])
def check_timer(timer_id):
    timer = active_timers.get(timer_id, None)
    if not timer:
        abort(404)
    
    if timer['active']:
        elapsed = (datetime.now() - datetime.fromisoformat(timer['start_time'])).total_seconds()
        remaining = max(0, timer['duration'] - elapsed)
        timer['remaining'] = remaining
        if remaining <= 0:
            timer['active'] = False
            timer['remaining'] = 0
    
    return jsonify(timer)

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5201')))
