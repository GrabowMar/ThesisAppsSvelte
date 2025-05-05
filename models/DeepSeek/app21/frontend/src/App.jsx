import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  // State management
  const [view, setView] = useState('recipes');
  const [recipes, setRecipes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    ingredients: [{ name: '', amount: '', unit: '', calories: 0, protein: 0, carbs: 0, fat: 0 }],
    instructions: [''],
    category: '',
    prep_time: 0,
    cook_time: 0,
    servings: 1
  });
  const [editingId, setEditingId] = useState(null);
  const [activeTimer, setActiveTimer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch data on mount
  useEffect(() => {
    fetchRecipes();
    fetchCategories();
  }, []);

  const fetchRecipes = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/recipes');
      const data = await response.json();
      setRecipes(data.recipes);
    } catch (err) {
      setError('Failed to fetch recipes');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/categories');
      const data = await response.json();
      setCategories(data.categories);
    } catch (err) {
      setError('Failed to fetch categories');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleIngredientChange = (index, field, value) => {
    const updatedIngredients = [...formData.ingredients];
    updatedIngredients[index][field] = value;
    setFormData({
      ...formData,
      ingredients: updatedIngredients
    });
  };

  const handleInstructionChange = (index, value) => {
    const updatedInstructions = [...formData.instructions];
    updatedInstructions[index] = value;
    setFormData({
      ...formData,
      instructions: updatedInstructions
    });
  };

  const addIngredient = () => {
    setFormData({
      ...formData,
      ingredients: [...formData.ingredients, { name: '', amount: '', unit: '', calories: 0, protein: 0, carbs: 0, fat: 0 }]
    });
  };

  const addInstruction = () => {
    setFormData({
      ...formData,
      instructions: [...formData.instructions, '']
    });
  };

  const removeIngredient = (index) => {
    const updatedIngredients = [...formData.ingredients];
    updatedIngredients.splice(index, 1);
    setFormData({
      ...formData,
      ingredients: updatedIngredients
    });
  };

  const removeInstruction = (index) => {
    const updatedInstructions = [...formData.instructions];
    updatedInstructions.splice(index, 1);
    setFormData({
      ...formData,
      instructions: updatedInstructions
    });
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      ingredients: [{ name: '', amount: '', unit: '', calories: 0, protein: 0, carbs: 0, fat: 0 }],
      instructions: [''],
      category: '',
      prep_time: 0,
      cook_time: 0,
      servings: 1
    });
    setEditingId(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const url = editingId ? `/api/recipes/${editingId}` : '/api/recipes';
      const method = editingId ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Request failed');
      }

      await fetchRecipes();
      resetForm();
      setView('recipes');
    } catch (err) {
      setError('Failed to save recipe');
    } finally {
      setLoading(false);
    }
  };

  const editRecipe = (recipe) => {
    setFormData({
      title: recipe.title,
      description: recipe.description,
      ingredients: recipe.ingredients,
      instructions: recipe.instructions,
      category: recipe.category,
      prep_time: recipe.prep_time,
      cook_time: recipe.cook_time,
      servings: recipe.servings
    });
    setEditingId(recipe.id);
    setView('edit');
  };

  const deleteRecipe = async (id) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/recipes/${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Delete failed');
      }

      await fetchRecipes();
    } catch (err) {
      setError('Failed to delete recipe');
    } finally {
      setLoading(false);
    }
  };

  const startTimer = async (recipeId, duration) => {
    try {
      const response = await fetch('/api/timer/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recipe_id: recipeId,
          duration: duration * 60 // convert minutes to seconds
        }),
      });

      const data = await response.json();
      setActiveTimer(data.timer_id);
    } catch (err) {
      setError('Failed to start timer');
    }
  };

  const checkTimer = async () => {
    if (!activeTimer) return;
    
    try {
      const response = await fetch(`/api/timer/${activeTimer}`);
      const data = await response.json();
      
      if (!data.active) {
        alert('Timer completed!');
        setActiveTimer(null);
      }
    } catch (err) {
      setError('Failed to check timer');
    }
  };

  useEffect(() => {
    let interval;
    if (activeTimer) {
      interval = setInterval(checkTimer, 1000);
    }
    return () => clearInterval(interval);
  }, [activeTimer]);

  // Render different views based on state
  const renderView = () => {
    switch (view) {
      case 'recipes':
        return (
          <div className="recipes-list">
            <h2>My Recipes</h2>
            <button onClick={() => { resetForm(); setView('add'); }}>Add New Recipe</button>
            
            {loading && <p>Loading...</p>}
            {error && <p className="error">{error}</p>}
            
            <div className="recipe-grid">
              {recipes.map(recipe => (
                <div key={recipe.id} className="recipe-card">
                  <h3>{recipe.title}</h3>
                  <p>Category: {recipe.category}</p>
                  <p>Prep: {recipe.prep_time} min | Cook: {recipe.cook_time} min</p>
                  <div className="recipe-actions">
                    <button onClick={() => editRecipe(recipe)}>Edit</button>
                    <button onClick={() => deleteRecipe(recipe.id)}>Delete</button>
                    <button onClick={() => startTimer(recipe.id, recipe.cook_time)}>Start Timer</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'add':
      case 'edit':
        return (
          <div className="recipe-form">
            <h2>{editingId ? 'Edit Recipe' : 'Add New Recipe'}</h2>
            <button onClick={() => { resetForm(); setView('recipes'); }}>Back to Recipes</button>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Title:</label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Description:</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="form-group">
                <label>Category:</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">Select a category</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Prep Time (min):</label>
                  <input
                    type="number"
                    name="prep_time"
                    value={formData.prep_time}
                    onChange={handleInputChange}
                    min="0"
                  />
                </div>
                
                <div className="form-group">
                  <label>Cook Time (min):</label>
                  <input
                    type="number"
                    name="cook_time"
                    value={formData.cook_time}
                    onChange={handleInputChange}
                    min="0"
                  />
                </div>
                
                <div className="form-group">
                  <label>Servings:</label>
                  <input
                    type="number"
                    name="servings"
                    value={formData.servings}
                    onChange={handleInputChange}
                    min="1"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <h3>Ingredients</h3>
                {formData.ingredients.map((ingredient, index) => (
                  <div key={index} className="ingredient-row">
                    <input
                      type="text"
                      placeholder="Name"
                      value={ingredient.name}
                      onChange={(e) => handleIngredientChange(index, 'name', e.target.value)}
                      required
                    />
                    <input
                      type="text"
                      placeholder="Amount"
                      value={ingredient.amount}
                      onChange={(e) => handleIngredientChange(index, 'amount', e.target.value)}
                      required
                    />
                    <input
                      type="text"
                      placeholder="Unit"
                      value={ingredient.unit}
                      onChange={(e) => handleIngredientChange(index, 'unit', e.target.value)}
                    />
                    <div className="nutrition-inputs">
                      <input
                        type="number"
                        placeholder="Calories"
                        value={ingredient.calories}
                        onChange={(e) => handleIngredientChange(index, 'calories', parseInt(e.target.value))}
                        min="0"
                      />
                      <input
                        type="number"
                        placeholder="Protein"
                        step="0.1"
                        value={ingredient.protein}
                        onChange={(e) => handleIngredientChange(index, 'protein', parseFloat(e.target.value))}
                        min="0"
                      />
                      <input
                        type="number"
                        placeholder="Carbs"
                        step="0.1"
                        value={ingredient.carbs}
                        onChange={(e) => handleIngredientChange(index, 'carbs', parseFloat(e.target.value))}
                        min="0"
                      />
                      <input
                        type="number"
                        placeholder="Fat"
                        step="0.1"
                        value={ingredient.fat}
                        onChange={(e) => handleIngredientChange(index, 'fat', parseFloat(e.target.value))}
                        min="0"
                      />
                    </div>
                    <button type="button" onClick={() => removeIngredient(index)}>Remove</button>
                  </div>
                ))}
                <button type="button" onClick={addIngredient}>Add Ingredient</button>
              </div>
              
              <div className="form-group">
                <h3>Instructions</h3>
                {formData.instructions.map((instruction, index) => (
                  <div key={index} className="instruction-row">
                    <textarea
                      placeholder={`Step ${index + 1}`}
                      value={instruction}
                      onChange={(e) => handleInstructionChange(index, e.target.value)}
                      required
                    />
                    <button type="button" onClick={() => removeInstruction(index)}>Remove</button>
                  </div>
                ))}
                <button type="button" onClick={addInstruction}>Add Step</button>
              </div>
              
              <button type="submit" disabled={loading}>
                {loading ? 'Saving...' : 'Save Recipe'}
              </button>
            </form>
          </div>
        );
      
      default:
        return <p>View not found</p>;
    }
  };

  return (
    <div className="app">
      <header>
        <h1>Recipe Management</h1>
        <nav>
          <button onClick={() => setView('recipes')}>Recipes</button>
        </nav>
      </header>
      
      <main>
        {renderView()}
      </main>
      {activeTimer && (
        <div className="timer-notification">
          Timer running... (Check console for updates)
        </div>
      )}
    </div>
  );
}

// Mount the app
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
