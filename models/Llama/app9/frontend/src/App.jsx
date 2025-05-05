// 1. Imports
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// 2. State Management
function App() {
  const [items, setItems] = useState([]);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [quantity, setQuantity] = useState(0);
  const [stockLevel, setStockLevel] = useState('');
  const [id, setId] = useState(null);

  // 3. Lifecycle Functions
  useEffect(() => {
    axios.get('/api/items')
      .then(response => {
        setItems(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  // 4. Event Handlers
  const handleSubmit = (event) => {
    event.preventDefault();
    if (id) {
      axios.put(`/api/items/${id}`, {
        name,
        category,
        quantity,
        stockLevel
      })
        .then(response => {
          setItems(items.map(item => item.id === id ? response.data : item));
          setId(null);
          setName('');
          setCategory('');
          setQuantity(0);
          setStockLevel('');
        })
        .catch(error => {
          console.error(error);
        });
    } else {
      axios.post('/api/items', {
        name,
        category,
        quantity,
        stockLevel
      })
        .then(response => {
          setItems([...items, response.data]);
          setName('');
          setCategory('');
          setQuantity(0);
          setStockLevel('');
        })
        .catch(error => {
          console.error(error);
        });
    }
  };

  const handleDelete = (itemId) => {
    axios.delete(`/api/items/${itemId}`)
      .then(response => {
        setItems(items.filter(item => item.id !== itemId));
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleEdit = (item) => {
    setId(item.id);
    setName(item.name);
    setCategory(item.category);
    setQuantity(item.quantity);
    setStockLevel(item.stockLevel);
  };

  // 5. API Calls
  // All API calls are made using Axios

  return (
    <div className="App">
      <h1>Inventory Management System</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Name:
          <input type="text" value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <br />
        <label>
          Category:
          <input type="text" value={category} onChange={(event) => setCategory(event.target.value)} />
        </label>
        <br />
        <label>
          Quantity:
          <input type="number" value={quantity} onChange={(event) => setQuantity(event.target.value)} />
        </label>
        <br />
        <label>
          Stock Level:
          <input type="text" value={stockLevel} onChange={(event) => setStockLevel(event.target.value)} />
        </label>
        <br />
        <button type="submit">{id ? 'Update' : 'Create'}</button>
      </form>
      <ul>
        {items.map(item => (
          <li key={item.id}>
            {item.name} ({item.category}) - Quantity: {item.quantity} - Stock Level: {item.stockLevel}
            <button onClick={() => handleEdit(item)}>Edit</button>
            <button onClick={() => handleDelete(item.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
