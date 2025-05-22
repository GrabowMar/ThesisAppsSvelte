# Backend Generation Prompt - Flask E-Commerce Cart Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/products`, `/api/cart`, `/api/checkout`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**E-Commerce Cart System Backend**  
A comprehensive Flask backend for e-commerce cart application, featuring product management, shopping cart operations, checkout process, and inventory tracking capabilities.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Product listing and management
- Shopping cart operations (add, remove, update)
- Checkout process with validation
- Order summary and management
- Inventory tracking and stock management
- Session-based cart persistence
- Price calculations and tax handling
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import uuid
from decimal import Decimal

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Cart Logic
# 5. Price Calculation Logic
# 6. Inventory Management
# 7. API Routes:
#    - GET /api/products (get all products)
#    - GET /api/products/<id> (get product details)
#    - GET /api/categories (get product categories)
#    - GET /api/cart (get current cart)
#    - POST /api/cart/add (add item to cart)
#    - PUT /api/cart/update (update cart item quantity)
#    - DELETE /api/cart/remove/<item_id> (remove from cart)
#    - DELETE /api/cart/clear (clear entire cart)
#    - POST /api/checkout (process checkout)
#    - GET /api/orders (get order history)
#    - GET /api/orders/<id> (get order details)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Product Management Routes

1. **GET /api/products**
   - Return paginated list of products
   - Support filtering by category, price range, availability
   - Include product details, pricing, and stock status

2. **GET /api/products/<id>**
   - Return specific product details
   - Include full description, images, specifications
   - Check inventory availability

3. **GET /api/categories**
   - Return list of product categories
   - Include category descriptions and product counts

### Cart Management Routes

4. **GET /api/cart**
   - Return current user's cart contents
   - Include item details, quantities, and totals
   - Calculate subtotal, tax, and total amounts

5. **POST /api/cart/add**
   - Accept: product_id, quantity
   - Add item to cart or update quantity if exists
   - Validate product availability and stock
   - Return updated cart summary

6. **PUT /api/cart/update**
   - Accept: item_id, quantity
   - Update specific cart item quantity
   - Validate stock availability
   - Return updated cart summary

7. **DELETE /api/cart/remove/<item_id>**
   - Remove specific item from cart
   - Return updated cart summary

8. **DELETE /api/cart/clear**
   - Remove all items from cart
   - Return confirmation response

### Checkout and Order Routes

9. **POST /api/checkout**
   - Accept: shipping_info, payment_method, billing_info
   - Validate cart contents and inventory
   - Calculate final pricing with taxes and shipping
   - Create order record
   - Update inventory quantities
   - Return order confirmation

10. **GET /api/orders**
    - Return user's order history
    - Include order summaries and status

11. **GET /api/orders/<id>**
    - Return specific order details
    - Include item details, pricing, and status

## Database Schema

```sql
Products table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- price (DECIMAL NOT NULL)
- category_id (INTEGER)
- stock_quantity (INTEGER DEFAULT 0)
- image_url (TEXT)
- is_active (BOOLEAN DEFAULT TRUE)
- created_at (TIMESTAMP)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)

Cart_Items table:
- id (TEXT PRIMARY KEY)
- session_id (TEXT NOT NULL)
- product_id (TEXT)
- quantity (INTEGER NOT NULL)
- added_at (TIMESTAMP)

Orders table:
- id (TEXT PRIMARY KEY)
- session_id (TEXT)
- total_amount (DECIMAL)
- tax_amount (DECIMAL)
- shipping_amount (DECIMAL)
- status (TEXT DEFAULT 'pending')
- shipping_address (TEXT)
- billing_address (TEXT)
- created_at (TIMESTAMP)

Order_Items table:
- id (TEXT PRIMARY KEY)
- order_id (TEXT)
- product_id (TEXT)
- quantity (INTEGER)
- price_at_time (DECIMAL)
- subtotal (DECIMAL)
```

## Business Logic Features

- **Inventory Management:** Real-time stock checking and updates
- **Price Calculations:** Subtotal, tax, shipping, and total calculations
- **Cart Persistence:** Session-based cart storage across page refreshes
- **Stock Validation:** Prevent overselling and handle out-of-stock scenarios
- **Order Processing:** Complete checkout workflow with validation
- **Tax Calculations:** Configurable tax rates and calculations
- **Shipping Logic:** Multiple shipping options and calculations

## Validation and Security Features

- Input validation for all cart operations
- Stock quantity validation before adding to cart
- Price integrity checks during checkout
- Session management for cart persistence
- SQL injection prevention
- Data sanitization for all inputs
- Order validation and confirmation

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, decimal handling libraries, etc.

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation and sanitization
   - Inventory management with concurrency handling
   - Price calculation accuracy with decimal precision
   - Session management for cart persistence
   - Order processing workflow
   - Database transaction management
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all e-commerce scenarios including inventory management, cart operations, checkout processing, and order management with proper validation and error handling.