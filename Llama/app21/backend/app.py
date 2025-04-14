from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# In-memory data store for demonstration purposes
recipes = [
    {"id": 1, "name": "Grilled Chicken", "ingredients": ["chicken", "salt", "pepper"], "instructions": "Grill chicken until cooked.", "category": "Main Course", "nutrition": {"calories": 350, "protein": 40}},
    {"id": 2, "name": "Vegetable Soup", "ingredients": ["vegetables", "broth"], "instructions": "Boil vegetables in broth.", "category": "Soup", "nutrition": {"calories": 150, "protein": 10}}
]

# API Routes
@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    return jsonify(recipes)

@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    new_recipe = request.json
    new_recipe['id'] = len(recipes) + 1
    recipes.append(new_recipe)
    return jsonify(new_recipe), 201

@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = next((r for r in recipes if r['id'] == recipe_id), None)
    if recipe is None:
        return jsonify({"error": "Recipe not found"}), 404
    return jsonify(recipe)

@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    recipe = next((r for r in recipes if r['id'] == recipe_id), None)
    if recipe is None:
        return jsonify({"error": "Recipe not found"}), 404
    updated_recipe = request.json
    recipe.update(updated_recipe)
    return jsonify(recipe)

@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    global recipes
    recipes = [r for r in recipes if r['id'] != recipe_id]
    return jsonify({"message": "Recipe deleted"})

@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = list(set(recipe['category'] for recipe in recipes))
    return jsonify(categories)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5041')))
