import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import './App.css';

const App = () => {
  const [recipes, setRecipes] = useState([]);

  useEffect(() => {
    fetch('/api/recipes')
      .then(response => response.json())
      .then(data => setRecipes(data))
      .catch(error => console.error('Error fetching recipes:', error));
  }, []);

  const createRecipe = (recipe) => {
    fetch('/api/recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recipe)
    })
    .then(response => response.json())
    .then(data => setRecipes([...recipes, data]))
    .catch(error => console.error('Error creating recipe:', error));
  };

  const updateRecipe = (recipe) => {
    fetch(`/api/recipes/${recipe.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recipe)
    })
    .then(response => response.json())
    .then(data => setRecipes(recipes.map(r => r.id === data.id ? data : r)))
    .catch(error => console.error('Error updating recipe:', error));
  };

  const deleteRecipe = (recipeId) => {
    fetch(`/api/recipes/${recipeId}`, {
      method: 'DELETE'
    })
    .then(() => setRecipes(recipes.filter(r => r.id !== recipeId)))
    .catch(error => console.error('Error deleting recipe:', error));
  };

  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/create">Create Recipe</Link></li>
          </ul>
        </nav>
        <Switch>
          <Route path="/" exact>
            <h1>Recipes</h1>
            <ul>
              {recipes.map(recipe => (
                <li key={recipe.id}>
                  <h2>{recipe.title}</h2>
                  <p>{recipe.ingredients}</p>
                  <p>{recipe.instructions}</p>
                  <p>{recipe.category}</p>
                  <p>{recipe.nutrition}</p>
                  <p>{recipe.timer}</p>
                  <button onClick={() => deleteRecipe(recipe.id)}>Delete</button>
                </li>
              ))}
            </ul>
          </Route>
          <Route path="/create">
            <h1>Create Recipe</h1>
            <CreateRecipeForm onCreate={createRecipe} />
          </Route>
        </Switch>
      </div>
    </Router>
  );
};

const CreateRecipeForm = ({ onCreate }) => {
  const [title, setTitle] = useState('');
  const [ingredients, setIngredients] = useState('');
  const [instructions, setInstructions] = useState('');
  const [category, setCategory] = useState('');
  const [nutrition, setNutrition] = useState('');
  const [timer, setTimer] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate({ title, ingredients, instructions, category, nutrition, timer });
    setTitle('');
    setIngredients('');
    setInstructions('');
    setCategory('');
    setNutrition('');
    setTimer('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" required />
      <input type="text" value={ingredients} onChange={(e) => setIngredients(e.target.value)} placeholder="Ingredients" required />
      <input type="text" value={instructions} onChange={(e) => setInstructions(e.target.value)} placeholder="Instructions" required />
      <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Category" required />
      <input type="text" value={nutrition} onChange={(e) => setNutrition(e.target.value)} placeholder="Nutrition" required />
      <input type="text" value={timer} onChange={(e) => setTimer(e.target.value)} placeholder="Timer" required />
      <button type="submit">Create Recipe</button>
    </form>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
