import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [checkoutTotal, setCheckoutTotal] = useState(0);

  // Fetch products from backend API
  useEffect(() => {
    fetch("http://localhost:5009/products")
      .then(response => response.json())
      .then(data => setProducts(data));
  }, []);

  // Add product to cart
  const handleAddToCart = (product) => {
    fetch("http://localhost:5009/cart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: product.id }),
    })
      .then(response => response.json())
      .then(data => {
        if (data.message === "Product added to cart") {
          setCart([...cart, product]);
        }
      });
  };

  // Remove product from cart
  const handleRemoveFromCart = (product) => {
    fetch("http://localhost:5009/cart", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: product.id }),
    })
      .then(response => response.json())
      .then(data => {
        if (data.message === "Product removed from cart") {
          setCart(cart.filter(item => item.id !== product.id));
        }
      });
  };

  // Checkout
  const handleCheckout = () => {
    fetch("http://localhost:5009/checkout", {
      method: "POST",
    })
      .then(response => response.json())
      .then(data => {
        if (data.message === "Checkout successful") {
          setCheckoutTotal(data.total_cost);
          setCart([]);
        }
      });
  };

  return (
    <div className="app">
      <h1>Products</h1>
      <ul>
        {products.map(product => (
          <li key={product.id}>
            {product.name} - ${product.price}
            <button onClick={() => handleAddToCart(product)}>Add to Cart</button>
          </li>
        ))}
      </ul>

      <h1>Cart</h1>
      <ul>
        {cart.map(product => (
          <li key={product.id}>
            {product.name} - ${product.price}
            <button onClick={() => handleRemoveFromCart(product)}>Remove</button>
          </li>
        ))}
      </ul>

      <button onClick={handleCheckout}>Checkout</button>
      {checkoutTotal > 0 && (
        <p>Checkout successful! Total: ${checkoutTotal}</p>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
