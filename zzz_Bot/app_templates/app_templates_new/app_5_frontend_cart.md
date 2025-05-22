# Frontend Generation Prompt - React E-Commerce Cart Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (products, cart, checkout, orders).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**E-Commerce Cart System Frontend**  
A modern React frontend for e-commerce cart application, featuring product browsing, shopping cart management, checkout process, and order tracking with responsive, user-friendly design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Product listing with search and filtering
- Shopping cart management (add, remove, update quantities)
- Checkout process with form validation
- Order summary and confirmation
- Inventory status display
- Price calculations and totals
- Responsive design
- Cart persistence across sessions

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (products, cart, checkout, orders, product-detail)
  // - products array with pagination
  // - cart items array
  // - currentProduct details
  // - categories array
  // - search and filter state
  // - checkout form data
  // - order history
  // - loading states
  // - error states

  // 4. Refs
  // - productGridRef for scrolling
  // - checkoutFormRef for validation
  
  // 5. Lifecycle Functions
  // - Load products and categories on mount
  // - Load cart from session
  // - Setup cart persistence
  
  // 6. Event Handlers
  // - handleAddToCart
  // - handleRemoveFromCart
  // - handleUpdateQuantity
  // - handleCheckout
  // - handleSearch
  // - handleCategoryFilter
  // - handleNavigation
  
  // 7. Cart Management Functions
  // - addToCart
  // - removeFromCart
  // - updateCartItem
  // - calculateCartTotal
  // - clearCart
  
  // 8. API Calls
  // - getProducts
  // - getProductDetails
  // - getCategories
  // - cartOperations
  // - processCheckout
  // - getOrders
  
  // 9. Utility Functions
  // - formatPrice
  // - formatDate
  // - validateCheckoutForm
  // - calculateTotals
  
  // 10. Render Methods
  // - renderProductGrid()
  // - renderProductDetail()
  // - renderCart()
  // - renderCheckout()
  // - renderOrderHistory()
  // - renderNavigation()
  
  return (
    <main className="ecommerce-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Product Listing View**
   - Header with logo, search, and cart icon
   - Category filter sidebar
   - Product grid with pagination
   - Product cards showing image, name, price, stock status
   - Add to cart buttons with quantity selectors
   - Search functionality with real-time filtering
   - Sort options (price, name, popularity)

2. **Product Detail View**
   - Large product image gallery
   - Product information (name, description, price)
   - Stock availability indicator
   - Quantity selector
   - Add to cart button
   - Product specifications
   - Related products section
   - Back to products navigation

3. **Shopping Cart View**
   - Cart items list with product details
   - Quantity update controls (+ / - buttons)
   - Remove item functionality
   - Price calculations (subtotal, tax, total)
   - Clear cart option
   - Continue shopping button
   - Proceed to checkout button
   - Empty cart state with call-to-action

4. **Checkout View**
   - Order summary with itemized list
   - Shipping information form
   - Billing information form
   - Payment method selection
   - Price breakdown (subtotal, tax, shipping, total)
   - Place order button
   - Form validation with error display
   - Loading state during order processing

5. **Order Confirmation/History View**
   - Order confirmation details
   - Order number and status
   - Itemized order summary
   - Shipping and billing information
   - Order history list (if multiple orders)
   - Continue shopping option

6. **Navigation Components**
   - Header with navigation menu
   - Shopping cart icon with item count
   - Search bar with suggestions
   - Category navigation
   - Mobile-responsive hamburger menu

## Shopping Cart Features

```javascript
// Cart management functionality:
const CartManagement = {
  // - Add products to cart with quantity validation
  // - Update item quantities with stock checking
  // - Remove individual items or clear entire cart
  // - Persist cart data across browser sessions
  // - Display real-time cart totals and item counts
  // - Handle out-of-stock scenarios gracefully
  // - Show cart preview on hover/click
};
```

## Checkout Process Features

- **Multi-step checkout** with form validation
- **Address validation** for shipping and billing
- **Payment method selection** (mock payment processing)
- **Order review** before final confirmation
- **Real-time price calculations** including tax and shipping
- **Inventory validation** before order completion
- **Error handling** for payment failures or inventory issues
- **Order confirmation** with tracking information

## UI/UX Requirements

- Clean, modern e-commerce design
- Responsive layout (mobile-first approach)
- Fast product browsing with lazy loading
- Smooth cart operations with visual feedback
- Loading states for all operations
- Error handling with user-friendly messages
- Search with autocomplete suggestions
- Product image optimization and lazy loading
- Accessibility compliance (ARIA labels, keyboard navigation)
- Shopping cart persistence across sessions

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Product API functions:
// - getProducts(page, category, search, sort)
// - getProductDetails(id)
// - getCategories()

// Cart API functions:
// - getCart()
// - addToCart(productId, quantity)
// - updateCartItem(itemId, quantity)
// - removeFromCart(itemId)
// - clearCart()

// Checkout API functions:
// - processCheckout(orderData)
// - getOrders()
// - getOrderDetails(orderId)
```

## Configuration Files

### vite.config.js
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: XXXX,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:YYYY',
        changeOrigin: true,
        secure: false,
      }
    }
  }
});
```

### index.html
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>E-Commerce Cart</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/App.jsx"></script>
  </body>
</html>
```

## Response Requirements

1. **Port Configuration**
   - Use `XXXX` for frontend port in vite.config.js
   - Proxy API calls to backend on port `YYYY`

2. **Dependencies**
   - Generate complete package.json with all necessary npm dependencies
   - Include React, Vite, and any additional libraries needed for e-commerce functionality

3. **Production Ready Features**
   - Comprehensive form validation
   - Error boundaries and fallbacks
   - Loading states for all operations
   - Responsive design with mobile optimization
   - Proper state management for cart persistence
   - Performance optimization (lazy loading, memoization)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, feedback)
   - SEO optimization for product pages

**Very important:** Your frontend should be feature rich, production ready, and provide excellent e-commerce user experience with intuitive product browsing, smooth cart operations, streamlined checkout process, and responsive design that works across all devices.