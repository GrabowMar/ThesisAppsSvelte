import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

// Main App Component
const App = () => {
  const [items, setItems] = useState([]); // Tracks inventory
  const [form, setForm] = useState({ name: "", category: "", stock: 0 }); // Form state
  const [error, setError] = useState(""); // Error state
  const [editId, setEditId] = useState(null); // For editing

  const API_BASE = "http://localhost:5257/api/items";

  // Fetch inventory on mount
  useEffect(() => {
    fetch(API_BASE)
      .then((res) => res.json())
      .then((data) => setItems(data))
      .catch((err) => setError("Failed to fetch inventory."));
  }, []);

  // Create or Update item
  const handleSubmit = (e) => {
    e.preventDefault();
    const method = editId ? "PUT" : "POST";
    const url = editId ? `${API_BASE}/${editId}` : API_BASE;

    fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    })
      .then((res) => res.json())
      .then((data) => {
        if (method === "POST") setItems([...items, data]);
        else
          setItems(items.map((item) => (item.id === editId ? data : item)));
        resetForm();
      })
      .catch(() => setError("Failed to save item."));
  };

  // Delete an item
  const handleDelete = (id) => {
    fetch(`${API_BASE}/${id}`, { method: "DELETE" })
      .then((res) => res.json())
      .then(() => setItems(items.filter((item) => item.id !== id)))
      .catch(() => setError("Failed to delete item."));
  };

  // Reset form and errors
  const resetForm = () => {
    setForm({ name: "", category: "", stock: 0 });
    setEditId(null);
    setError("");
  };

  // Set up edit mode
  const handleEdit = (item) => {
    setEditId(item.id);
    setForm({ name: item.name, category: item.category, stock: item.stock });
  };

  // Render Component
  return (
    <div className="App">
      <h1>Inventory Management</h1>

      {error && <p className="error">{error}</p>}

      {/* Form */}
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          type="text"
          placeholder="Category"
          value={form.category}
          onChange={(e) => setForm({ ...form, category: e.target.value })}
        />
        <input
          type="number"
          placeholder="Stock"
          value={form.stock}
          onChange={(e) => setForm({ ...form, stock: +e.target.value })}
        />
        <button>{editId ? "Update" : "Add Item"}</button>
        {editId && <button onClick={resetForm}>Cancel</button>}
      </form>

      {/* Inventory Table */}
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Stock</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.category}</td>
              <td>{item.stock}</td>
              <td>
                <button onClick={() => handleEdit(item)}>Edit</button>
                <button onClick={() => handleDelete(item.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Mount app to DOM
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
