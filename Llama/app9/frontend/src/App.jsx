import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [items, setItems] = useState([]);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [stockLevel, setStockLevel] = useState(0);
  const [itemId, setItemId] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5017/items')
      .then(response => response.json())
      .then(data => setItems(data));
  }, []);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (itemId) {
      // Update existing item
      fetch(`http://localhost:5017/items/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, category, stock_level: stockLevel }),
      })
        .then(response => response.json())
        .then(data => {
          setItems(items.map(item => item.id === data.id ? data : item));
          setItemId(null);
          setName('');
          setCategory('');
          setStockLevel(0);
        });
    } else {
      // Create new item
      fetch('http://localhost:5017/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, category, stock_level: stockLevel }),
      })
        .then(response => response.json())
        .then(data => {
          setItems([...items, data]);
          setName('');
          setCategory('');
          setStockLevel(0);
        });
    }
  };

  const handleDelete = (id) => {
    fetch(`http://localhost:5017/items/${id}`, { method: 'DELETE' })
      .then(() => {
        setItems(items.filter(item => item.id !== id));
      });
  };

  const handleUpdate = (id) => {
    const item = items.find(item => item.id === id);
    setItemId(id);
    setName(item.name);
    setCategory(item.category);
    setStockLevel(item.stock_level);
  };

  return (
    <div className="app">
      <h1>Inventory Management System</h1>
      <form onSubmit={handleSubmit}>
        <label>Name:</label>
        <input type="text" value={name} onChange={(event) => setName(event.target.value)} />
        <br />
        <label>Category:</label>
        <input type="text" value={category} onChange={(event) => setCategory(event.target.value)} />
        <br />
        <label>Stock Level:</label>
        <input type="number" value={stockLevel} onChange={(event) => setStockLevel(event.target.valueAsNumber)} />
        <br />
        <button type="submit">{itemId ? 'Update' : 'Create'}</button>
      </form>
      <ul>
        {items.map(item => (
          <li key={item.id}>
            {item.name} ({item.category}) - Stock Level: {item.stock_level}
            <button onClick={() => handleUpdate(item.id)}>Update</button>
            <button onClick={() => handleDelete(item.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
