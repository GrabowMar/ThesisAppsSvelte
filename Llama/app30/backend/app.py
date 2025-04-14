# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (using in-memory dictionary for simplicity)
recipes = {}
recipe_id = 1

# 4. Authentication Logic (not implemented for simplicity)

# 5. Utility Functions
def validate_recipe(data):
    required_fields = ['name', 'ingredients', 'instructions', 'category', 'nutrition', 'cookingTime']
    if not all(field in data for field in required_fields):
        return False
    return True

# 6. API Routes
@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    return jsonify(list(recipes.values()))

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    global recipe_id
    data = request.json
    if not validate_recipe(data):
        return jsonify({'error': 'Invalid recipe data'}), 400
    recipe = {
        'id': recipe_id,
        'name': data['name'],
        'ingredients': data['ingredients'],
        'instructions': data['instructions'],
        'category': data['category'],
        'nutrition': data['nutrition'],
        'cookingTime': data['cookingTime'],
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    recipes[recipe_id] = recipe
    recipe_id += 1
    return jsonify(recipe), 201

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = recipes.get(recipe_id)
    if recipe is None:
        return jsonify({'error': 'Recipe not found'}), 404
    return jsonify(recipe)

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    recipe = recipes.get(recipe_id)
    if recipe is None:
        return jsonify({'error': 'Recipe not found'}), 404
    data = request.json
    if not validate_recipe(data):
        return jsonify({'error': 'Invalid recipe data'}), 400
    recipe['name'] = data['name']
    recipe['ingredients'] = data['ingredients']
    recipe['instructions'] = data['instructions']
    recipe['category'] = data['category']
    recipe['nutrition'] = data['nutrition']
    recipe['cookingTime'] = data['cookingTime']
    return jsonify(recipe)

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    recipe = recipes.get(recipe_id)
    if recipe is None:
        return jsonify({'error': 'Recipe not found'}), 404
    del recipes[recipe_id]
    return jsonify({'message': 'Recipe deleted'})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5059')))
