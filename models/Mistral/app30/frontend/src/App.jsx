import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import axios from 'axios';
import './App.css';
const App = () => {
  const [recipes, setRecipes] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    ingredients: '',
    instructions: '',
    category: '',
    nutrition: '',
    cooking_time: ''
  });
useEffect(() => {
  axios.get('/api/recipes')
    .then(response => setRecipes(response.data))
    .catch(error => console.error('Error fetching recipes:', error));
}, []);
const handleChange = (e) => {
  const { name, value } = e.target;
  setFormData({
    ...formData,
    [name]: value
  });
};

const handleSubmit = (e) => {
  e.preventDefault();
  axios.post('/api/recipes', formData)
    .then(response => {
      setRecipes([...recipes, response.data]);
      setFormData({
        title: '',
        description: '',
        ingredients: '',
        instructions: '',
        category: '',
        nutrition: '',
        cooking_time: ''
      });
    })
    .catch(error => console.error('Error creating recipe:', error));
};
const deleteRecipe = (recipeId) => {
  axios.delete(`/api/recipes/${recipeId}`)
    .then(() => setRecipes(recipes.filter(recipe => recipe.id !== recipeId)))
    .catch(error => console.error('Error deleting recipe:', error));
};
return (
  <Router>
    <div className="app">
      <Routes>
        <Route path="/" element={
          <div>
            <h1>Recipe Management System</h1>
            <form onSubmit={handleSubmit}>
              <input type="text" name="title" placeholder="Title" value={formData.title} onChange={handleChange} required />
              <textarea name="description" placeholder="Description" value={formData.description} onChange={handleChange}></textarea>
              <textarea name="ingredients" placeholder="Ingredients" value={formData.ingredients} onChange={handleChange} required></textarea>
              <textarea name="instructions" placeholder="Instructions" value={formData.instructions} onChange={handleChange} required></textarea>
              <input type="text" name="category" placeholder="Category" value={formData.category} onChange={handleChange} />
              <textarea name="nutrition" placeholder="Nutrition" value={formData.nutrition} onChange={handleChange}></textarea>
              <input type="number" name="cooking_time" placeholder="Cooking Time" value={formData.cooking_time} onChange={handleChange} />
              <button type="submit">Add Recipe</button>
            </form>
            <ul>
              {recipes.map(recipe => (
                <li key={recipe.id}>
                  <h2>{recipe.title}</h2>
                  <p>{recipe.description}</p>
                  <button onClick={() => deleteRecipe(recipe.id)}>Delete</button>
                </li>
              ))}
            </ul>
          </div>
        } />
      </Routes>
    </div>
  </Router>
);
ReactDOM.createRoot(document.getElementById('root')).render(<App />);

