# Backend Generation Prompt - Flask CRUD Inventory Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/items`, `/api/categories`, `/api/inventory`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**CRUD Inventory System Backend**  
A comprehensive Flask backend for inventory management application, featuring complete CRUD operations, stock tracking, categorization, alerts system, and advanced search/filtering capabilities.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Full CRUD operations for inventory items
- Real-time inventory tracking and stock management
- Category management and organization
- Stock level alerts and notifications
- Advanced search and filtering capabilities
- Stock movement history and audit trails
- Supplier and vendor management
- Reports and analytics endpoints
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
from decimal import Decimal
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Inventory Logic
# 5. Alert System
# 6. Utility Functions
# 7. API Routes:
#    - GET /api/items (list all items with pagination/filtering)
#    - GET /api/items/<id> (get specific item)
#    - POST /api/items (create new item)
#    - PUT /api/items/<id> (update item)
#    - DELETE /api/items/<id> (delete item)
#    - GET /api/categories (get all categories)
#    - POST /api/categories (create category)
#    - PUT /api/categories/<id> (update category)
#    - DELETE /api/categories/<id> (delete category)
#    - GET /api/inventory/low-stock (get low stock alerts)
#    - POST /api/inventory/adjust (adjust stock levels)
#    - GET /api/inventory/movements (get stock movement history)
#    - GET /api/search (search items)
#    - GET /api/reports/summary (inventory summary)
#    - GET /api/reports/analytics (inventory analytics)
#    - GET /api/suppliers (get suppliers)
#    - POST /api/suppliers (create supplier)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Item CRUD Operations

1. **GET /api/items**
   - Return paginated list of inventory items
   - Support filtering by category, stock status, supplier
   - Support sorting by name, price, stock, date
   - Include item metadata and current stock levels

2. **GET /api/items/<id>**
   - Return specific item with full details
   - Include stock history and movement records
   - Show supplier information and pricing

3. **POST /api/items**
   - Create new inventory item
   - Accept: name, description, category_id, price, initial_stock, min_stock, supplier_id
   - Validate input and generate unique SKU
   - Return created item with generated ID

4. **PUT /api/items/<id>**
   - Update existing item
   - Accept: name, description, category_id, price, min_stock, supplier_id
   - Track change history
   - Return updated item

5. **DELETE /api/items/<id>**
   - Delete item from inventory
   - Implement soft delete with recovery option
   - Handle stock movements cleanup
   - Return confirmation response

### Category Management Routes

6. **GET /api/categories**
   - Return list of item categories
   - Include item counts for each category
   - Support hierarchical categories

7. **POST /api/categories**
   - Create new category
   - Accept: name, description, parent_id
   - Validate uniqueness
   - Return created category

8. **PUT /api/categories/<id>**
   - Update category details
   - Accept: name, description, parent_id
   - Return updated category

9. **DELETE /api/categories/<id>**
   - Delete category
   - Handle items in deleted category
   - Return confirmation

### Inventory Management Routes

10. **GET /api/inventory/low-stock**
    - Return items with stock below minimum threshold
    - Include alert severity levels
    - Support threshold customization

11. **POST /api/inventory/adjust**
    - Adjust stock levels for items
    - Accept: item_id, quantity_change, reason, notes
    - Create stock movement record
    - Return updated stock level

12. **GET /api/inventory/movements**
    - Return stock movement history
    - Support filtering by item, date range, movement type
    - Include movement details and reasons

### Search and Analytics Routes

13. **GET /api/search**
    - Search items by name, SKU, description
    - Accept: query, category_filter, stock_filter
    - Return ranked search results

14. **GET /api/reports/summary**
    - Return inventory summary statistics
    - Include total items, total value, low stock count
    - Category breakdown and trends

15. **GET /api/reports/analytics**
    - Return detailed analytics data
    - Stock turnover rates, value analysis
    - Trend analysis and forecasting data

### Supplier Management Routes

16. **GET /api/suppliers**
    - Return list of suppliers
    - Include supplier details and item counts

17. **POST /api/suppliers**
    - Create new supplier
    - Accept: name, contact_info, address
    - Return created supplier

## Database Schema

```sql
Items table:
- id (TEXT PRIMARY KEY)
- sku (TEXT UNIQUE NOT NULL)
- name (TEXT NOT NULL)
- description (TEXT)
- category_id (INTEGER)
- supplier_id (INTEGER)
- price (DECIMAL)
- cost_price (DECIMAL)
- current_stock (INTEGER DEFAULT 0)
- min_stock_level (INTEGER DEFAULT 0)
- max_stock_level (INTEGER)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- is_active (BOOLEAN DEFAULT TRUE)

Categories table:
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE NOT NULL)
- description (TEXT)
- parent_id (INTEGER)
- created_at (TIMESTAMP)

Suppliers table:
- id (INTEGER PRIMARY KEY)
- name (TEXT NOT NULL)
- contact_person (TEXT)
- email (TEXT)
- phone (TEXT)
- address (TEXT)
- created_at (TIMESTAMP)

Stock_Movements table:
- id (TEXT PRIMARY KEY)
- item_id (TEXT)
- movement_type (TEXT) -- 'in', 'out', 'adjustment'
- quantity (INTEGER)
- previous_stock (INTEGER)
- new_stock (INTEGER)
- reason (TEXT)
- notes (TEXT)
- created_at (TIMESTAMP)

Stock_Alerts table:
- id (TEXT PRIMARY KEY)
- item_id (TEXT)
- alert_type (TEXT) -- 'low_stock', 'out_of_stock'
- threshold_value (INTEGER)
- current_stock (INTEGER)
- created_at (TIMESTAMP)
- resolved_at (TIMESTAMP)
- is_active (BOOLEAN DEFAULT TRUE)
```

## Inventory Management Features

- **Real-time stock tracking** with automatic updates
- **Low stock alerts** with configurable thresholds
- **Stock movement logging** for audit trails
- **Bulk operations** for multiple items
- **SKU generation** with customizable formats
- **Price history** tracking and analysis
- **Stock valuation** calculations
- **Inventory turnover** metrics

## Alert System Features

- **Configurable stock thresholds** per item
- **Multi-level alert severity** (warning, critical)
- **Alert aggregation** and summarization
- **Automatic alert resolution** when stock replenished
- **Alert history** and reporting
- **Email notifications** (configurable)

## Search and Analytics Features

- **Full-text search** across item attributes
- **Advanced filtering** by multiple criteria
- **Stock analytics** and reporting
- **Trend analysis** for stock movements
- **Value-based reporting** for inventory worth
- **Export functionality** for reports

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, decimal handling, analytics libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Input validation and sanitization
   - CRUD operation validation
   - Stock level consistency checks
   - Transaction management for stock operations
   - Performance optimization for large inventories
   - Audit logging for all operations
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all inventory management scenarios including CRUD operations, stock tracking, alert management, and analytics with proper validation and audit trails.