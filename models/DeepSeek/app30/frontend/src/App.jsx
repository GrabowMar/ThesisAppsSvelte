import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [recipes, setRecipes] = useState([]);
  const [currentRecipe, setCurrentRecipe] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [view, setView] = useState('recipes'); // 'recipes', 'create', 'edit', 'meal-plan'
  const [categories, setCategories] = useState([]);
  const [mealPlan, setMealPlan] = useState({});
  const [timer, setTimer] = useState(null);

  useEffect(() => {
    fetchRecipes();
    fetchCategories();
    fetchMealPlan();
  }, []);

  const fetchRecipes = async () => {
    try {
      const response = await fetch('/api/recipes');
      const data = await response.json();
      setRecipes(data);
    } catch (error) {
      console.error('Error fetching recipes:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/categories');
      const data = await response.json();
      setCategories(data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchMealPlan = async () => {
    try {
      const response = await fetch('/api/meal-plan');
      const data = await response.json();
      setMealPlan(data);
    } catch (error) {
      console.error('Error fetching meal plan:', error);
    }
  };

  const handleCreateRecipe = async (recipeData) => {
    try {
      const response = await fetch('/api/recipes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(recipeData),
      });
      if (response.ok) {
        await fetchRecipes();
        setView('recipes');
      }
    } catch (error) {
      console.error('Error creating recipe:', error);
    }
  };

  const handleUpdateRecipe = async (recipeData) => {
    try {
      const response = await fetch(`/api/recipes/${recipeData.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(recipeData),
      });
      if (response.ok) {
        await fetchRecipes();
        setView('recipes');
        setCurrentRecipe(null);
        setIsEditing(false);
      }
    } catch (error) {
      console.error('Error updating recipe:', error);
    }
  };

  const handleAddToMealPlan = async (date, mealType, recipeId) => {
    try {
      const response = await fetch('/api/meal-plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ date, meal_type: mealType, recipe_id: recipeId }),
      });
      if (response.ok) {
        await fetchMealPlan();
      }
    } catch (error) {
      console.error('Error adding to meal plan:', error);
    }
  };

  const startTimer = async (duration) => {
    try {
      const response = await fetch('/api/timer/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ duration }),
      });
      const data = await response.json();
      if (response.ok) {
        setTimer(data);
      }
    } catch (error) {
      console.error('Error starting timer:', error);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Recipe Management</h1>
        <nav>
          <button onClick={() => setView('recipes')}>All Recipes</button>
          <button onClick={() => { setView('create'); setCurrentRecipe(null); setIsEditing(false); }}>
            Create Recipe
          </button>
          <button onClick={() => setView('meal-plan')}>Meal Plan</button>
        </nav>
      </header>

      <main className="main-content">
        {view === 'recipes' && (
          <RecipesList
            recipes={recipes}
            onViewRecipe={(recipe) => { setCurrentRecipe(recipe); setView('edit'); }}
          />
        )}

        {view === 'create' && (
          <RecipeForm
            categories={categories}
            onSubmit={handleCreateRecipe}
            isEditing={false}
          />
        )}

        {view === 'edit' && currentRecipe && (
          <RecipeForm
            recipe={currentRecipe}
            categories={categories}
            onSubmit={handleUpdateRecipe}
            isEditing={true}
          />
        )}

        {view === 'meal-plan' && (
          <MealPlanView
            mealPlan={mealPlan}
            recipes={recipes}
            onAddToMealPlan={handleAddToMealPlan}
          />
        )}
      </main>

      {timer && (
        <div className="timer-overlay">
          <div className="timer">
            <h3>Timer</h3>
            <p>Ends at: {new Date(timer.ends_at).toLocaleTimeString()}</p>
            <button onClick={() => setTimer(null)}>Dismiss</button>
          </div>
        </div>
      )}
    </div>
  );
}

function RecipesList({ recipes, onViewRecipe }) {
  return (
    <div className="recipes-list">
      <h2>All Recipes</h2>
      {recipes.length === 0 ? (
        <p>No recipes found. Create one to get started!</p>
      ) : (
        <ul>
          {recipes.map(recipe => (
            <li key={recipe.id} className="recipe-card">
              <h3>{recipe.title}</h3>
              <p>{recipe.category}</p>
              <p>Prep: {recipe.prep_time} min | Cook: {recipe.cook_time} min | Serves: {recipe.servings}</p>
              <button onClick={() => onViewRecipe(recipe)}>View/Edit</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function RecipeForm({ recipe, categories, onSubmit, isEditing }) {
  const initialRecipeData = recipe || {
    title: '',
    description: '',
    category: '',
    ingredients: [{ name: '', amount: '', unit: '' }],
    instructions: '',
    prep_time: 0,
    cook_time: 0,
    servings: 1
  };

  const [formData, setFormData] = useState(initialRecipeData);

  const handleIngredientChange = (index, field, value) => {
    const newIngredients = [...formData.ingredients];
    newIngredients[index][field] = value;
    setFormData({ ...formData, ingredients: newIngredients });
  };

  const addIngredient = () => {
    setFormData({
      ...formData,
      ingredients: [...formData.ingredients, { name: '', amount: '', unit: '' }]
    });
  };

  const removeIngredient = (index) => {
    if (formData.ingredients.length > 1) {
      const newIngredients = formData.ingredients.filter((_, i) => i !== index);
      setFormData({ ...formData, ingredients: newIngredients });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="recipe-form">
      <h2>{isEditing ? 'Edit Recipe' : 'Create New Recipe'}</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Title</label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label>Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Category</label>
          <select
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            required
          >
            <option value="">Select a category</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        <div className="ingredients-section">
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
              <button type="button" onClick={() => removeIngredient(index)}>Remove</button>
            </div>
          ))}
          <button type="button" onClick={addIngredient}>Add Ingredient</button>
        </div>

        <div className="form-group">
          <label>Instructions</label>
          <textarea
            value={formData.instructions}
            onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
            required
          />
        </div>

        <div className="form-group-row">
          <div>
            <label>Prep Time (minutes)</label>
            <input
              type="number"
              value={formData.prep_time}
              onChange={(e) => setFormData({ ...formData, prep_time: parseInt(e.target.value) || 0 })}
            />
          </div>
          <div>
            <label>Cook Time (minutes)</label>
            <input
              type="number"
              value={formData.cook_time}
              onChange={(e) => setFormData({ ...formData, cook_time: parseInt(e.target.value) || 0 })}
            />
          </div>
          <div>
            <label>Servings</label>
            <input
              type="number"
              value={formData.servings}
              onChange={(e) => setFormData({ ...formData, servings: parseInt(e.target.value) || 1 })}
              min="1"
            />
          </div>
        </div>

        <button type="submit">{isEditing ? 'Update Recipe' : 'Create Recipe'}</button>
        <button type="button" onClick={() => {}}>Cancel</button>
      </form>
    </div>
  );
}

function MealPlanView({ mealPlan, recipes, onAddToMealPlan }) {
  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const mealTypes = ['Breakfast', 'Lunch', 'Dinner'];

  const [selectedDay, setSelectedDay] = useState(null);
  const [selectedMealType, setSelectedMealType] = useState(null);
  const [selectedRecipe, setSelectedRecipe] = useState(null);

  const handleAddMeal = () => {
    if (selectedDay && selectedMealType && selectedRecipe) {
      onAddToMealPlan(selectedDay, selectedMealType, selectedRecipe);
      setSelectedDay(null);
      setSelectedMealType(null);
      setSelectedRecipe(null);
    }
  };

  return (
    <div className="meal-plan-view">
      <h2>Meal Plan</h2>
      
      <div className="add-meal-form">
        <h3>Add Meal to Plan</h3>
        <div>
          <select value={selectedDay || ''} onChange={(e) => setSelectedDay(e.target.value)}>
            <option value="">Select day</option>
            {daysOfWeek.map(day => (
              <option key={day} value={day}>{day}</option>
            ))}
          </select>
          
          <select value={selectedMealType || ''} onChange={(e) => setSelectedMealType(e.target.value)}>
            <option value="">Select meal type</option>
            {mealTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          
          <select value={selectedRecipe || ''} onChange={(e) => setSelectedRecipe(parseInt(e.target.value))}>
            <option value="">Select recipe</option>
            {recipes.map(recipe => (
              <option key={recipe.id} value={recipe.id}>{recipe.title}</option>
            ))}
          </select>
          
          <button onClick={handleAddMeal} disabled={!selectedDay || !selectedMealType || !selectedRecipe}>
            Add to Meal Plan
          </button>
        </div>
      </div>
      
      <div className="meal-plan-grid">
        {daysOfWeek.map(day => (
          <div key={day} className="day-card">
            <h3>{day}</h3>
            {mealTypes.map(type => {
              const recipeId = mealPlan[day]?.[type];
              const recipe = recipes.find(r => r.id === recipeId);
              return (
                <div key={type} className="meal-slot">
                  <h4>{type}</h4>
                  {recipe ? (
                    <>
                      <p>{recipe.title}</p>
                      <p>Prep: {recipe.prep_time} min, Cook: {recipe.cook_time} min</p>
                    </>
                  ) : (
                    <p>No meal planned</p>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

// Mount the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
