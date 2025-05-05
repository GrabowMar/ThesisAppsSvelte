import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [recipes, setRecipes] = useState([]);
    const [newRecipe, setNewRecipe] = useState({ name: '', ingredients: '', instructions: '', category: '', nutrition: { calories: 0, protein: 0 } });
    const [selectedRecipe, setSelectedRecipe] = useState(null);

    useEffect(() => {
        fetch('/api/recipes')
            .then(response => response.json())
            .then(data => setRecipes(data));
    }, []);

    const handleCreateRecipe = () => {
        fetch('/api/recipes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newRecipe)
        })
        .then(response => response.json())
        .then(data => {
            setRecipes([...recipes, data]);
            setNewRecipe({ name: '', ingredients: '', instructions: '', category: '', nutrition: { calories: 0, protein: 0 } });
        });
    };

    const handleUpdateRecipe = () => {
        if (!selectedRecipe) return;
        fetch(`/api/recipes/${selectedRecipe.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(selectedRecipe)
        })
        .then(response => response.json())
        .then(data => {
            setRecipes(recipes.map(recipe => recipe.id === data.id ? data : recipe));
            setSelectedRecipe(null);
        });
    };

    const handleDeleteRecipe = (id) => {
        fetch(`/api/recipes/${id}`, { method: 'DELETE' })
        .then(() => {
            setRecipes(recipes.filter(recipe => recipe.id !== id));
        });
    };

    const handleSelectRecipe = (recipe) => {
        setSelectedRecipe(recipe);
    };

    return (
        <div className="app">
            <h1>Recipe Management</h1>
            <div className="recipe-list">
                <h2>Recipes</h2>
                <ul>
                    {recipes.map(recipe => (
                        <li key={recipe.id}>
                            <span onClick={() => handleSelectRecipe(recipe)}>{recipe.name}</span>
                            <button onClick={() => handleDeleteRecipe(recipe.id)}>Delete</button>
                        </li>
                    ))}
                </ul>
            </div>
            <div className="recipe-form">
                <h2>{selectedRecipe ? 'Edit Recipe' : 'Create Recipe'}</h2>
                <input type="text" placeholder="Name" value={selectedRecipe ? selectedRecipe.name : newRecipe.name} onChange={(e) => selectedRecipe ? setSelectedRecipe({ ...selectedRecipe, name: e.target.value }) : setNewRecipe({ ...newRecipe, name: e.target.value })} />
                <input type="text" placeholder="Ingredients" value={selectedRecipe ? selectedRecipe.ingredients.join(', ') : newRecipe.ingredients} onChange={(e) => selectedRecipe ? setSelectedRecipe({ ...selectedRecipe, ingredients: e.target.value.split(', ') }) : setNewRecipe({ ...newRecipe, ingredients: e.target.value })} />
                <textarea placeholder="Instructions" value={selectedRecipe ? selectedRecipe.instructions : newRecipe.instructions} onChange={(e) => selectedRecipe ? setSelectedRecipe({ ...selectedRecipe, instructions: e.target.value }) : setNewRecipe({ ...newRecipe, instructions: e.target.value })} />
                <input type="text" placeholder="Category" value={selectedRecipe ? selectedRecipe.category : newRecipe.category} onChange={(e) => selectedRecipe ? setSelectedRecipe({ ...selectedRecipe, category: e.target.value }) : setNewRecipe({ ...newRecipe, category: e.target.value })} />
                <input type="number" placeholder="Calories" value={selectedRecipe ? selectedRecipe.nutrition.calories : newRecipe.nutrition.calories} onChange={(e) => selectedRecipe ? setSelectedRecipe({ ...selectedRecipe, nutrition: { ...selectedRecipe.nutrition, calories: e.target.value } }) : setNewRecipe({ ...newRecipe, nutrition: { ...newRecipe.nutrition, calories: e.target.value } })} />
                <input type="number" placeholder="Protein" value={selectedRecipe ? selectedRecipe.nutrition.protein : newRecipe.nutrition.protein} onChange={(e) => selectedRecipe ? setSelectedRecipe({ ...selectedRecipe, nutrition: { ...selectedRecipe.nutrition, protein: e.target.value } }) : setNewRecipe({ ...newRecipe, nutrition: { ...newRecipe.nutrition, protein: e.target.value } })} />
                {selectedRecipe ? (
                    <button onClick={handleUpdateRecipe}>Update Recipe</button>
                ) : (
                    <button onClick={handleCreateRecipe}>Create Recipe</button>
                )}
            </div>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
