import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [recipes, setRecipes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [newRecipe, setNewRecipe] = useState({
    title: "",
    ingredients: "",
    instructions: "",
    category: "",
    nutrition: {},
  });

  // Fetch all recipes
  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/recipes`)
      .then((res) => res.json())
      .then((data) => setRecipes(data.recipes))
      .catch((error) => console.error("Error fetching recipes:", error));
  }, []);

  // Fetch categories
  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/categories`)
      .then((res) => res.json())
      .then((data) => setCategories(data.categories))
      .catch((error) => console.error("Error fetching categories:", error));
  }, []);

  // Create a new recipe
  const handleCreateRecipe = () => {
    fetch(`${import.meta.env.VITE_API_URL}/api/recipes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newRecipe),
    })
      .then((res) => res.json())
      .then((data) => {
        alert(data.message);
        setNewRecipe({
          title: "",
          ingredients: "",
          instructions: "",
          category: "",
          nutrition: {},
        });
        loadRecipes();
      })
      .catch((error) => console.error("Error creating recipe:", error));
  };

  // Helper: Reload recipes
  const loadRecipes = () => {
    fetch(`${import.meta.env.VITE_API_URL}/api/recipes`)
      .then((res) => res.json())
      .then((data) => setRecipes(data.recipes))
      .catch((error) => console.error("Error fetching recipes:", error));
  };

  return (
    <div className="app">
      <h1>Recipe Management System</h1>
      <h2>Categories</h2>
      <ul>
        {categories.map((cat, index) => (
          <li key={index}>{cat}</li>
        ))}
      </ul>
      <h2>Recipes</h2>
      {recipes.length === 0 ? (
        <p>No recipes found!</p>
      ) : (
        <ul>
          {recipes.map((recipe) => (
            <li key={recipe.id}>
              {recipe.title} - {recipe.category}
            </li>
          ))}
        </ul>
      )}
      <h2>Create a New Recipe</h2>
      <div>
        <label>Title: </label>
        <input
          type="text"
          value={newRecipe.title}
          onChange={(e) =>
            setNewRecipe({ ...newRecipe, title: e.target.value })
          }
        />
        <label>Ingredients: </label>
        <input
          type="text"
          value={newRecipe.ingredients}
          onChange={(e) =>
            setNewRecipe({ ...newRecipe, ingredients: e.target.value })
          }
        />
        <button onClick={handleCreateRecipe}>Submit</button>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
