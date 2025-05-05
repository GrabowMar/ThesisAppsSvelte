import { useState, useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import './App.css'

function App() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [order, setOrder] = useState(null)
  const [page, setPage] = useState('products')
  const [error, setError] = useState('')
  
  // Fetch initial data
  useEffect(() => {
    fetch('/api/products')
      .then(res => res.json())
      .then(data => setProducts(data))
      .catch(err => setError('Failed to load products'))
      
    fetch('/api/cart', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setCart(data))
      .catch(() => setError('Failed to load cart'))
  }, [])

  const addToCart = (productId) => {
    fetch('/api/cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId }),
      credentials: 'include'
    })
    .then(res => res.json())
    .then(updatedCart => setCart(updatedCart))
    .catch(() => setError('Failed to update cart'))
  }

  const handleCheckout = (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const customer = {
      name: formData.get('name'),
      email: formData.get('email')
    }

    fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(customer),
      credentials: 'include'
    })
    .then(res => res.json())
    .then(orderData => {
      setOrder(orderData)
      setPage('order')
      setCart([])
    })
    .catch(() => setError('Checkout failed'))
  }

  const getTotal = () => cart.reduce((sum, item) => {
    const product = products.find(p => p.id === item.product_id)
    return sum + (product?.price || 0) * item.quantity
  }, 0).toFixed(2)

  return (
    <main>
      <nav>
        <button onClick={() => setPage('products')}>Products</button>
        <button onClick={() => setPage('cart')}>
          Cart ({cart.length})
        </button>
      </nav>
      
      {error && <div className="error">{error}</div>}

      {page === 'products' && (
        <div className="products-grid">
          {products.map(product => (
            <div key={product.id} className="product-card">
              <h3>{product.name}</h3>
              <p>${product.price} | Stock: {product.stock}</p>
              <button 
                onClick={() => addToCart(product.id)}
                disabled={product.stock <= 0}
              >
                Add to Cart
              </button>
            </div>
          ))}
        </div>
      )}

      {page === 'cart' && (
        <div className="cart-page">
          {cart.length === 0 ? (
            <p>Your cart is empty</p>
          ) : (
            <>
              <div className="cart-items">
                {cart.map(item => {
                  const product = products.find(p => p.id === item.product_id)
                  return (
                    <div key={item.product_id} className="cart-item">
                      <h4>{product?.name}</h4>
                      <p>Qty: {item.quantity} × ${product?.price}</p>
                    </div>
                  )
                })}
              </div>
              <div className="cart-summary">
                <h3>Total: ${getTotal()}</h3>
                <button onClick={() => setPage('checkout')}>
                  Proceed to Checkout
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {page === 'checkout' && (
        <form onSubmit={handleCheckout} className="checkout-form">
          <h2>Checkout</h2>
          <label>
            Name:
            <input type="text" name="name" required />
          </label>
          <label>
            Email:
            <input type="email" name="email" required />
          </label>
          <button type="submit">Place Order</button>
        </form>
      )}

      {page === 'order' && order && (
        <div className="order-confirmation">
          <h2>Order Confirmation</h2>
          <p>Order ID: {order.id}</p>
          <p>Date: {new Date(order.date).toLocaleString()}</p>
          <p>Total: ${order.total.toFixed(2)}</p>
        </div>
      )}
    </main>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
