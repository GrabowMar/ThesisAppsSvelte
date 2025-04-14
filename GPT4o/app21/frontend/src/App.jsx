// Imports
import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

// Backend API URL
const API_URL = "http://localhost:5281/api/recipes";

const App = () => {
  // State Management
  const [recipes, setRecipes] = useState([]);
  const [form, setForm] = useState({
    name: "",
    ingredients: "",
    category: "",
    timer: "",
    nutrition: { calories: 0, protein: 0, fat: 0, carbs: 0 },
  });

  const [error, setError] = useState("");

  // Fetch Recipes
  const fetchRecipes = async () => {
    const res = await fetch(API_URL);
    const data = await res.json();
    if (res.ok) setRecipes(data.recipes);
    else setError(data.error);
  };

  // Add Recipe
  const addRecipe = async (e) => {
    e.preventDefault();
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    if (res.ok) {
      setRecipes([...recipes, data.recipe]);
      setForm({ name: "", ingredients: "", category: "", timer: "", nutrition: {} });
    } else setError(data.error || "Failed to add recipe!");
  };

  // Delete Recipe
  const deleteRecipe = async (id) => {
    const res = await fetch(`${API_URL}/${id}`, { method: "DELETE" });
    if (res.ok) fetchRecipes();
    else setError("Failed to delete recipe!");
  };

  useEffect(() => {
    fetchRecipes();
  }, []);

  // Render
  return (
    <div className="App">
      <h1>Recipe Management</h1>

      {error && <div className="error">{error}</div>}

      {/* Recipe Listing */}
      <ul>
        {recipes.map((recipe) => (
          <li key={recipe.id}>
            <h3>{recipe.name}</h3>
            <p>Ingredients: {recipe.ingredients.join(", ")}</p>
            <p>Category: {recipe.category}</p>
            <button onClick={() => deleteRecipe(recipe.id)}>Delete</button>
          </li>
        ))}
      </ul>

      {/* Add Recipe */}
      <form onSubmit={addRecipe}>
        <h3>Add Recipe</h3>
        <input
          type="text"
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <input
          type="text"
          placeholder="Ingredients (comma-separated)"
          value={form.ingredients}
          onChange={(e) =>
            setForm({ ...form, ingredients: e.target.value.split(",") })
          }
          required
        />
        <input
          type="text"
          placeholder="Category"
          value={form.category}
          onChange={(e) => setForm({ ...form, category: e.target.value })}
        />
        <input
          type="number"
          placeholder="Timer (minutes)"
          value={form.timer}
          onChange={(e) => setForm({ ...form, timer: e.target.value })}
        />
        <button type="submit">Add Recipe</button>
      </form>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
