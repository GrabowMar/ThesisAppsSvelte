# Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# App Configuration
app = Flask(__name__)
CORS(app)

# In-Memory Data Storage for Simplicity
recipes = [
    {
        "id": 1,
        "name": "Spaghetti Carbonara",
        "ingredients": ["Spaghetti", "Eggs", "Bacon", "Parmesan Cheese", "Salt", "Pepper"],
        "category": "Dinner",
        "nutrition": {"calories": 500, "protein": 20, "fat": 15, "carbs": 50},
        "timer": 15
    }
]

# Routes

@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """Retrieve all recipes."""
    return jsonify({"recipes": recipes}), 200


@app.route('/api/recipes', methods=['POST'])
def add_recipe():
    """Add a new recipe."""
    data = request.json
    if not data.get("name") or not data.get("ingredients"):
        return jsonify({"error": "Recipe name and ingredients are required!"}), 400

    new_recipe = {
        "id": len(recipes) + 1,
        "name": data["name"],
        "ingredients": data["ingredients"],
        "category": data.get("category", "Uncategorized"),
        "nutrition": data.get("nutrition", {}),
        "timer": data.get("timer", 0),
    }
    recipes.append(new_recipe)
    return jsonify({"message": "Recipe added successfully!", "recipe": new_recipe}), 201


@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
def edit_recipe(recipe_id):
    """Edit an existing recipe."""
    data = request.json
    recipe = next((r for r in recipes if r["id"] == recipe_id), None)
    if not recipe:
        return jsonify({"error": "Recipe not found!"}), 404

    recipe.update({
        "name": data.get("name", recipe["name"]),
        "ingredients": data.get("ingredients", recipe["ingredients"]),
        "category": data.get("category", recipe["category"]),
        "nutrition": data.get("nutrition", recipe["nutrition"]),
        "timer": data.get("timer", recipe["timer"]),
    })
    return jsonify({"message": "Recipe updated successfully!", "recipe": recipe}), 200


@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Delete a recipe."""
    global recipes
    recipes = [r for r in recipes if r["id"] != recipe_id]
    return jsonify({"message": "Recipe deleted successfully!"}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found!"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle server errors."""
    return jsonify({"error": "Internal Server Error!"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5281')))
