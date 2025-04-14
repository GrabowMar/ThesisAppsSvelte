import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [recipes, setRecipes] = useState([]);
  const [recipe, setRecipe] = useState({
    name: '',
    ingredients: '',
    instructions: '',
    category: '',
    nutrition: '',
    cookingTime: ''
  });
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    fetch('/api/recipes')
      .then(response => response.json())
      .then(data => setRecipes(data));
  }, []);

  const handleInputChange = (e) => {
    setRecipe({ ...recipe, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editing) {
      fetch(`/api/recipes/${editing}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(recipe)
      })
        .then(response => response.json())
        .then(data => {
          setRecipes(recipes.map(r => r.id === editing ? data : r));
          setEditing(null);
          setRecipe({
            name: '',
            ingredients: '',
            instructions: '',
            category: '',
            nutrition: '',
            cookingTime: ''
          });
        });
    } else {
      fetch('/api/recipes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(recipe)
      })
        .then(response => response.json())
        .then(data => {
          setRecipes([...recipes, data]);
          setRecipe({
            name: '',
            ingredients: '',
            instructions: '',
            category: '',
            nutrition: '',
            cookingTime: ''
          });
        });
    }
  };

  const handleEdit = (id) => {
    const recipeToEdit = recipes.find(r => r.id === id);
    setRecipe(recipeToEdit);
    setEditing(id);
  };

  const handleDelete = (id) => {
    fetch(`/api/recipes/${id}`, { method: 'DELETE' })
      .then(() => setRecipes(recipes.filter(r => r.id !== id)));
  };

  return (
    <div className="App">
      <h1>Recipe Management System</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" name="name" value={recipe.name} onChange={handleInputChange} placeholder="Name" />
        <input type="text" name="ingredients" value={recipe.ingredients} onChange={handleInputChange} placeholder="Ingredients" />
        <input type="text" name="instructions" value={recipe.instructions} onChange={handleInputChange} placeholder="Instructions" />
        <input type="text" name="category" value={recipe.category} onChange={handleInputChange} placeholder="Category" />
        <input type="text" name="nutrition" value={recipe.nutrition} onChange={handleInputChange} placeholder="Nutrition" />
        <input type="text" name="cookingTime" value={recipe.cookingTime} onChange={handleInputChange} placeholder="Cooking Time" />
        <button type="submit">{editing ? 'Update' : 'Create'}</button>
      </form>
      <ul>
        {recipes.map(recipe => (
          <li key={recipe.id}>
            <h2>{recipe.name}</h2>
            <p>Ingredients: {recipe.ingredients}</p>
            <p>Instructions: {recipe.instructions}</p>
            <p>Category: {recipe.category}</p>
            <p>Nutrition: {recipe.nutrition}</p>
            <p>Cooking Time: {recipe.cookingTime}</p>
            <button onClick={() => handleEdit(recipe.id)}>Edit</button>
            <button onClick={() => handleDelete(recipe.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
