import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
    const [items, setItems] = useState([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [formData, setFormData] = useState({ name: "", category: "Uncategorized", stock: 0 });

    // Fetch all items on component mount
    useEffect(() => {
        fetchItems();
    }, []);

    const fetchItems = async () => {
        const response = await fetch("http://localhost:5177/api/items");
        const data = await response.json();
        setItems(data);
    };

    const handleAddItem = async (e) => {
        e.preventDefault();
        const response = await fetch("http://localhost:5177/api/items", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
        });
        if (response.ok) {
            fetchItems();
            setFormData({ name: "", category: "Uncategorized", stock: 0 });
        }
    };

    const handleDeleteItem = async (id) => {
        const response = await fetch(`http://localhost:5177/api/items/${id}`, { method: "DELETE" });
        if (response.ok) fetchItems();
    };

    const filteredItems = items.filter(item =>
        item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.category.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="container">
            <h1>Inventory Management System</h1>
            <input
                type="text"
                placeholder="Search items..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
            />
            <form onSubmit={handleAddItem}>
                <input
                    type="text"
                    placeholder="Item Name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                />
                <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                    <option value="Electronics">Electronics</option>
                    <option value="Clothing">Clothing</option>
                    <option value="Uncategorized">Uncategorized</option>
                </select>
                <input
                    type="number"
                    placeholder="Stock"
                    value={formData.stock}
                    onChange={(e) => setFormData({ ...formData, stock: parseInt(e.target.value) })}
                    required
                />
                <button type="submit">Add Item</button>
            </form>
            <ul>
                {filteredItems.map(item => (
                    <li key={item.id} className={item.alert ? "alert" : ""}>
                        {item.name} ({item.category}) - Stock: {item.stock}
                        <button onClick={() => handleDeleteItem(item.id)}>Delete</button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

// Mount the app
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
