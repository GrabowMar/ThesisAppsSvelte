import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const API_BASE = "http://localhost:5249/api";

const App = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [view, setView] = useState("products"); // "products" | "cart" | "checkout"

  // Fetch Products
  useEffect(() => {
    fetch(`${API_BASE}/products`)
      .then((res) => res.json())
      .then((data) => setProducts(data.products))
      .catch((err) => console.error("Error fetching products:", err));
  }, []);

  // Fetch Cart Items
  const fetchCart = () => {
    fetch(`${API_BASE}/cart`)
      .then((res) => res.json())
      .then((data) => setCart(data.cart))
      .catch((err) => console.error("Error fetching cart:", err));
  };

  const addToCart = (productId, quantity = 1) => {
    fetch(`${API_BASE}/cart/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, quantity }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          fetchCart(); // Refresh cart
        } else {
          alert(data.message);
        }
      })
      .catch((err) => console.error("Error adding to cart:", err));
  };

  const handleCheckout = () => {
    fetch(`${API_BASE}/cart/checkout`, { method: "POST" })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          fetchCart(); // Refresh cart
          alert(data.message);
        } else {
          alert("Checkout failed!");
        }
      })
      .catch((err) => console.error("Error during checkout:", err));
  };

  // Main App UI
  return (
    <div className="App">
      <header>
        <h1>E-Commerce Cart System</h1>
        <nav>
          <button onClick={() => setView("products")}>Products</button>
          <button onClick={() => { fetchCart(); setView("cart"); }}>Cart</button>
        </nav>
      </header>
      <main>
        {view === "products" && (
          <div className="product-list">
            <h2>Products</h2>
            {products.map((product) => (
              <div key={product.id} className="product-item">
                <h3>{product.name}</h3>
                <p>Price: ${product.price.toFixed(2)}</p>
                <p>Stock: {product.stock}</p>
                <button onClick={() => addToCart(product.id)}>Add to Cart</button>
              </div>
            ))}
          </div>
        )}
        {view === "cart" && (
          <div className="cart">
            <h2>Cart</h2>
            {cart.length === 0 ? (
              <p>Your cart is empty!</p>
            ) : (
              <ul>
                {cart.map((item) => (
                  <li key={item.id}>
                    {item.name} x {item.quantity} (${item.price.toFixed(2)})
                  </li>
                ))}
              </ul>
            )}
            {cart.length > 0 && <button onClick={handleCheckout}>Checkout</button>}
          </div>
        )}
      </main>
    </div>
  );
};

// Mount to the DOM
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);
