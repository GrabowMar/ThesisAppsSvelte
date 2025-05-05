import { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState({});

  useEffect(() => {
    axios.get('/api/products')
      .then(response => {
        setProducts(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleAddToCart = (product) => {
    axios.post('/api/cart', { product_id: product.name })
      .then(response => {
        axios.get('/api/cart')
          .then(response => {
            setCart(response.data.cart);
          })
          .catch(error => {
            console.error(error);
          });
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleCheckout = () => {
    axios.post('/api/checkout')
      .then(response => {
        setOrders(orders => ({ ...orders, [response.data.order_id]: response.data.order }));
        setCart([]);
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <div>
      <h1>Products</h1>
      <ul>
        {products.map(product => (
          <li key={product.name}>
            {product.name} - {product.price}
            <button onClick={() => handleAddToCart(product)}>Add to Cart</button>
          </li>
        ))}
      </ul>
      <h1>Cart</h1>
      <ul>
        {cart.map(product => (
          <li key={product.name}>
            {product.name} - {product.price}
          </li>
        ))}
      </ul>
      <button onClick={handleCheckout}>Checkout</button>
      <h1>Orders</h1>
      <ul>
        {Object.keys(orders).map(orderId => (
          <li key={orderId}>
            <h2>Order {orderId}</h2>
            <ul>
              {orders[orderId].map(product => (
                <li key={product.name}>
                  {product.name} - {product.price}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
