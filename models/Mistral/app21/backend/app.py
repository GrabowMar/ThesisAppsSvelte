from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Sample data
recipes = []

# Utility function to generate a unique ID
def generate_id():
    return len(recipes) + 1

# API Routes
@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    return jsonify(recipes)

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    data = request.get_json()
    recipe = {
        'id': generate_id(),
        'title': data['title'],
        'ingredients': data['ingredients'],
        'instructions': data['instructions'],
        'category': data['category'],
        'nutrition': data['nutrition'],
        'timer': data['timer']
    }
    recipes.append(recipe)
    return jsonify(recipe), 201

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    data = request.get_json()
    recipe = next((recipe for recipe in recipes if recipe['id'] == recipe_id), None)
    if recipe:
        recipe.update(data)
        return jsonify(recipe)
    return jsonify({'error': 'Recipe not found'}), 404

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    global recipes
    recipes = [recipe for recipe in recipes if recipe['id'] != recipe_id]
    return jsonify({'result': True})

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5121')))
