import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);

  useEffect(() => {
    fetchProducts();
    fetchCart();
  }, []);

  const fetchProducts = async () => {
    const response = await fetch("http://localhost:5169/api/products");
    const data = await response.json();
    setProducts(data);
  };

  const fetchCart = async () => {
    const response = await fetch("http://localhost:5169/api/cart");
    const data = await response.json();
    setCart(data);
  };

  const addToCart = async (productId) => {
    const response = await fetch("http://localhost:5169/api/cart/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ productId, quantity: 1 }),
    });
    const data = await response.json();
    setCart(data);
  };

  const removeFromCart = async (productId) => {
    const response = await fetch(`http://localhost:5169/api/cart/remove/${productId}`, {
      method: "DELETE",
    });
    const data = await response.json();
    setCart(data);
  };

  const checkout = async () => {
    const response = await fetch("http://localhost:5169/api/checkout", {
      method: "POST",
    });
    const data = await response.json();
    alert(data.message);
    setCart([]);
  };

  return (
    <div className="app">
      <h1>E-Commerce Cart</h1>
      <div className="product-list">
        <h2>Products</h2>
        {products.map((product) => (
          <div key={product.id} className="product">
            <h3>{product.name}</h3>
            <p>${product.price} | Stock: {product.stock}</p>
            <button onClick={() => addToCart(product.id)}>Add to Cart</button>
          </div>
        ))}
      </div>
      <div className="cart">
        <h2>Cart</h2>
        {cart.map((item) => (
          <div key={item.id} className="cart-item">
            <h3>{item.name}</h3>
            <p>${item.price} | Quantity: {item.quantity}</p>
            <button onClick={() => removeFromCart(item.id)}>Remove</button>
          </div>
        ))}
        {cart.length > 0 && <button onClick={checkout}>Checkout</button>}
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
