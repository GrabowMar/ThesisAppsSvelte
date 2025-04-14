from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

## Sample in-memory storage
recipes = []  # Stores Recipe data
categories = ["Breakfast", "Lunch", "Dinner", "Snack"]  # Default categories

## Routes

# Home route
@app.route("/")
def home():
    return jsonify({"message": "Welcome to Recipe Management System!"})

# Get all recipes
@app.route("/api/recipes", methods=["GET"])
def get_recipes():
    return jsonify({"recipes": recipes})

# Create a new recipe
@app.route("/api/recipes", methods=["POST"])
def create_recipe():
    data = request.json
    if not data.get("title") or not data.get("ingredients"):
        return jsonify({"error": "Title and Ingredients are required!"}), 400
    recipe_id = len(recipes) + 1
    recipes.append({
        "id": recipe_id,
        "title": data["title"],
        "ingredients": data["ingredients"],
        "instructions": data.get("instructions", ""),
        "category": data.get("category", "Uncategorized"),
        "nutrition": data.get("nutrition", {}),
    })
    return jsonify({"message": "Recipe created successfully!"}), 201

# Edit a recipe
@app.route("/api/recipes/<int:recipe_id>", methods=["PUT"])
def update_recipe(recipe_id):
    data = request.json
    for recipe in recipes:
        if recipe["id"] == recipe_id:
            recipe["title"] = data.get("title", recipe["title"])
            recipe["ingredients"] = data.get("ingredients", recipe["ingredients"])
            recipe["instructions"] = data.get("instructions", recipe["instructions"])
            recipe["category"] = data.get("category", recipe["category"])
            recipe["nutrition"] = data.get("nutrition", recipe["nutrition"])
            return jsonify({"message": "Recipe updated successfully!"})
    return jsonify({"error": "Recipe not found!"}), 404

# Delete a recipe
@app.route("/api/recipes/<int:recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id):
    global recipes
    filtered_recipes = [recipe for recipe in recipes if recipe["id"] != recipe_id]
    if len(filtered_recipes) == len(recipes):
        return jsonify({"error": "Recipe not found!"}), 404
    recipes = filtered_recipes
    return jsonify({"message": "Recipe deleted successfully!"})

# Get recipe categories
@app.route("/api/categories", methods=["GET"])
def get_categories():
    return jsonify({"categories": categories})

# Run Server
if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5299")))
