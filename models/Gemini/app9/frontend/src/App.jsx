// app/frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [inventory, setInventory] = useState([]);
  const [newItem, setNewItem] = useState({ name: '', category: '', stock: 0, price: 0 });
  const [selectedItem, setSelectedItem] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentView, setCurrentView] = useState('inventory'); // 'inventory' | 'add' | 'edit'

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      const response = await fetch('/api/inventory');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setInventory(data);
    } catch (error) {
      console.error("Failed to fetch inventory:", error);
      alert("Failed to fetch inventory. Check the console for details.");
    }
  };

  const handleInputChange = (e) => {
    setNewItem({ ...newItem, [e.target.name]: e.target.value });
  };

  const handleCreateItem = async () => {
    try {
      const response = await fetch('/api/inventory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newItem),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const createdItem = await response.json();
      setInventory([...inventory, createdItem]);
      setNewItem({ name: '', category: '', stock: 0, price: 0 }); // Clear the form
      setCurrentView('inventory'); // Navigate back to inventory view
    } catch (error) {
      console.error("Failed to create item:", error);
      alert("Failed to create item. Check the console for details.");
    }
  };

  const handleSelectItem = (item) => {
    setSelectedItem(item);
    setEditMode(true);
    setCurrentView('edit');
  };

  const handleUpdateItem = async () => {
    try {
      const response = await fetch(`/api/inventory/${selectedItem.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(selectedItem),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const updatedItem = await response.json();
      setInventory(inventory.map(item => (item.id === updatedItem.id ? updatedItem : item)));
      setSelectedItem(null);
      setEditMode(false);
      setCurrentView('inventory'); // Navigate back to inventory view

    } catch (error) {
      console.error("Failed to update item:", error);
      alert("Failed to update item. Check the console for details.");
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (window.confirm("Are you sure you want to delete this item?")) {
      try {
        const response = await fetch(`/api/inventory/${itemId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        setInventory(inventory.filter(item => item.id !== itemId));

      } catch (error) {
        console.error("Failed to delete item:", error);
        alert("Failed to delete item. Check the console for details.");
      }
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const filteredInventory = inventory.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const renderInventoryView = () => (
    <div>
      <h2>Inventory</h2>
      <input
        type="text"
        placeholder="Search items..."
        value={searchTerm}
        onChange={handleSearch}
      />
      <button onClick={() => setCurrentView('add')}>Add New Item</button>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Stock</th>
            <th>Price</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredInventory.map(item => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.category}</td>
              <td>{item.stock}</td>
              <td>${item.price}</td>
              <td>
                <button onClick={() => handleSelectItem(item)}>Edit</button>
                <button onClick={() => handleDeleteItem(item.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderAddView = () => (
    <div>
      <h2>Add New Item</h2>
      <form>
        <label>Name:</label>
        <input type="text" name="name" value={newItem.name} onChange={handleInputChange} /><br />
        <label>Category:</label>
        <input type="text" name="category" value={newItem.category} onChange={handleInputChange} /><br />
        <label>Stock:</label>
        <input type="number" name="stock" value={newItem.stock} onChange={handleInputChange} /><br />
        <label>Price:</label>
        <input type="number" name="price" value={newItem.price} onChange={handleInputChange} /><br />
        <button type="button" onClick={handleCreateItem}>Create Item</button>
        <button type="button" onClick={() => setCurrentView('inventory')}>Cancel</button>
      </form>
    </div>
  );

  const renderEditView = () => (
    <div>
      <h2>Edit Item</h2>
      {selectedItem && (
        <form>
          <label>Name:</label>
          <input
            type="text"
            name="name"
            value={selectedItem.name}
            onChange={(e) => setSelectedItem({ ...selectedItem, name: e.target.value })}
          /><br />
          <label>Category:</label>
          <input
            type="text"
            name="category"
            value={selectedItem.category}
            onChange={(e) => setSelectedItem({ ...selectedItem, category: e.target.value })}
          /><br />
          <label>Stock:</label>
          <input
            type="number"
            name="stock"
            value={selectedItem.stock}
            onChange={(e) => setSelectedItem({ ...selectedItem, stock: parseInt(e.target.value) })}
          /><br />
          <label>Price:</label>
          <input
            type="number"
            name="price"
            value={selectedItem.price}
            onChange={(e) => setSelectedItem({ ...selectedItem, price: parseFloat(e.target.value) })}
          /><br />
          <button type="button" onClick={handleUpdateItem}>Update Item</button>
          <button type="button" onClick={() => setCurrentView('inventory')}>Cancel</button>
        </form>
      )}
    </div>
  );


  let content;
  if (currentView === 'inventory') {
    content = renderInventoryView();
  } else if (currentView === 'add') {
    content = renderAddView();
  } else if (currentView === 'edit') {
    content = renderEditView();
  }

  return (
    <div className="App">
      <h1>Inventory Management</h1>
      {content}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);

export default App;
