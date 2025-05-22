# Backend Generation Prompt - Flask Personal Finance Tracker Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/transactions`, `/api/budgets`, `/api/goals`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Personal Finance Management System Backend**  
A comprehensive Flask backend for personal finance application, featuring income/expense tracking, budget management, financial goal setting, transaction categorization, and detailed financial analytics with security and data protection.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete income and expense tracking system
- Budget creation and monitoring with alerts
- Financial goal setting and progress tracking
- Advanced expense categorization and tagging
- Comprehensive financial reports and analytics
- Transaction management with search and filtering
- Recurring transaction handling
- Financial insights and spending patterns
- User authentication and profile management
- Data export and import capabilities
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
import json
from decimal import Decimal
import calendar
import csv
import io

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Financial Calculations
# 5. Budget Analysis
# 6. Goal Tracking Logic
# 7. API Routes:
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
#    - GET /api/transactions (get transactions with filtering)
#    - GET /api/transactions/<id> (get specific transaction)
#    - POST /api/transactions (create new transaction)
#    - PUT /api/transactions/<id> (update transaction)
#    - DELETE /api/transactions/<id> (delete transaction)
#    - GET /api/categories (get expense categories)
#    - POST /api/categories (create category)
#    - PUT /api/categories/<id> (update category)
#    - DELETE /api/categories/<id> (delete category)
#    - GET /api/budgets (get user budgets)
#    - POST /api/budgets (create budget)
#    - GET /api/budgets/<id> (get budget details)
#    - PUT /api/budgets/<id> (update budget)
#    - DELETE /api/budgets/<id> (delete budget)
#    - GET /api/goals (get financial goals)
#    - POST /api/goals (create goal)
#    - PUT /api/goals/<id> (update goal)
#    - DELETE /api/goals/<id> (delete goal)
#    - POST /api/goals/<id>/contribute (add contribution)
#    - GET /api/reports/summary (get financial summary)
#    - GET /api/reports/monthly (get monthly report)
#    - GET /api/reports/category (get category breakdown)
#    - GET /api/reports/trends (get spending trends)
#    - GET /api/insights (get financial insights)
#    - POST /api/import (import transactions)
#    - GET /api/export (export data)
#    - GET /api/recurring (get recurring transactions)
#    - POST /api/recurring (create recurring transaction)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, currency_preference
   - Validate input and create user account
   - Hash password securely
   - Initialize default categories and budgets
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info and financial summary

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include financial preferences and settings

### Transaction Management Routes

5. **GET /api/transactions**
   - Return paginated list of transactions
   - Support filtering by date range, category, type, amount
   - Support sorting by date, amount, category
   - Include running balance calculations

6. **GET /api/transactions/<id>**
   - Return specific transaction with full details
   - Include category info and related data

7. **POST /api/transactions**
   - Create new transaction
   - Accept: amount, type, category_id, description, date, tags
   - Validate amount and category
   - Update account balances
   - Return created transaction

8. **PUT /api/transactions/<id>**
   - Update existing transaction
   - Require authentication and ownership
   - Recalculate balances if amount changed
   - Return updated transaction

9. **DELETE /api/transactions/<id>**
   - Delete transaction
   - Require authentication and ownership
   - Update account balances
   - Return confirmation

### Category Management Routes

10. **GET /api/categories**
    - Return list of expense/income categories
    - Include usage statistics and budget allocations
    - Support hierarchical categories

11. **POST /api/categories**
    - Create new category
    - Accept: name, type, color, parent_id, budget_limit
    - Return created category

12. **PUT /api/categories/<id>**
    - Update category details
    - Accept: name, color, budget_limit
    - Return updated category

13. **DELETE /api/categories/<id>**
    - Delete category
    - Handle transactions in deleted category
    - Return confirmation

### Budget Management Routes

14. **GET /api/budgets**
    - Return user's budgets with current status
    - Include spent amounts and remaining budgets
    - Show budget alerts and warnings

15. **POST /api/budgets**
    - Create new budget
    - Accept: name, amount, period, categories, start_date
    - Validate budget parameters
    - Return created budget

16. **GET /api/budgets/<id>**
    - Return detailed budget information
    - Include spending breakdown and trends
    - Show budget performance metrics

17. **PUT /api/budgets/<id>**
    - Update budget details
    - Accept: amount, period, categories
    - Recalculate budget status
    - Return updated budget

18. **DELETE /api/budgets/<id>**
    - Delete budget
    - Return confirmation

### Financial Goals Routes

19. **GET /api/goals**
    - Return user's financial goals
    - Include progress and target dates
    - Show achievement status

20. **POST /api/goals**
    - Create new financial goal
    - Accept: name, target_amount, target_date, goal_type
    - Return created goal

21. **PUT /api/goals/<id>**
    - Update goal details
    - Accept: name, target_amount, target_date
    - Return updated goal

22. **DELETE /api/goals/<id>**
    - Delete goal
    - Return confirmation

23. **POST /api/goals/<id>/contribute**
    - Add contribution to goal
    - Accept: amount, date, notes
    - Update goal progress
    - Return updated goal status

### Reporting and Analytics Routes

24. **GET /api/reports/summary**
    - Return financial summary for specified period
    - Include income, expenses, net worth, savings rate
    - Show key financial metrics

25. **GET /api/reports/monthly**
    - Return monthly financial report
    - Include month-over-month comparisons
    - Break down by categories

26. **GET /api/reports/category**
    - Return category-wise spending breakdown
    - Include trends and comparisons
    - Support custom date ranges

27. **GET /api/reports/trends**
    - Return spending and income trends
    - Include seasonal patterns and predictions
    - Provide insights and recommendations

28. **GET /api/insights**
    - Return personalized financial insights
    - Include spending pattern analysis
    - Suggest optimization opportunities

### Data Import/Export Routes

29. **POST /api/import**
    - Import transactions from CSV/OFX files
    - Validate and categorize imported data
    - Return import summary and errors

30. **GET /api/export**
    - Export user data in various formats
    - Support CSV, PDF, JSON formats
    - Include transactions, budgets, goals

### Recurring Transactions Routes

31. **GET /api/recurring**
    - Return scheduled recurring transactions
    - Include next occurrence dates
    - Show active/inactive status

32. **POST /api/recurring**
    - Create recurring transaction template
    - Accept: transaction_data, frequency, end_date
    - Return created recurring transaction

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- currency (TEXT DEFAULT 'USD')
- timezone (TEXT)
- created_at (TIMESTAMP)
- monthly_income (DECIMAL)
- financial_goals_total (DECIMAL DEFAULT 0)

Categories table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT NOT NULL)
- type (TEXT) -- 'income', 'expense'
- color (TEXT)
- parent_id (TEXT)
- budget_limit (DECIMAL)
- is_default (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)

Transactions table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- amount (DECIMAL NOT NULL)
- type (TEXT) -- 'income', 'expense', 'transfer'
- category_id (TEXT)
- description (TEXT)
- date (DATE)
- tags (TEXT) -- JSON array
- payment_method (TEXT)
- location (TEXT)
- notes (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

Budgets table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT NOT NULL)
- amount (DECIMAL NOT NULL)
- period (TEXT) -- 'monthly', 'weekly', 'yearly'
- start_date (DATE)
- end_date (DATE)
- categories (TEXT) -- JSON array of category IDs
- alert_threshold (DECIMAL DEFAULT 0.8)
- created_at (TIMESTAMP)

Budget_Tracking table:
- id (TEXT PRIMARY KEY)
- budget_id (TEXT)
- period_start (DATE)
- period_end (DATE)
- budgeted_amount (DECIMAL)
- spent_amount (DECIMAL DEFAULT 0)
- remaining_amount (DECIMAL)
- status (TEXT) -- 'on_track', 'warning', 'exceeded'

Financial_Goals table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- name (TEXT NOT NULL)
- description (TEXT)
- target_amount (DECIMAL NOT NULL)
- current_amount (DECIMAL DEFAULT 0)
- target_date (DATE)
- goal_type (TEXT) -- 'savings', 'debt', 'investment'
- priority (INTEGER DEFAULT 1)
- is_achieved (BOOLEAN DEFAULT FALSE)
- created_at (TIMESTAMP)

Goal_Contributions table:
- id (TEXT PRIMARY KEY)
- goal_id (TEXT)
- amount (DECIMAL NOT NULL)
- contribution_date (DATE)
- notes (TEXT)
- created_at (TIMESTAMP)

Recurring_Transactions table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- template_name (TEXT)
- amount (DECIMAL NOT NULL)
- type (TEXT)
- category_id (TEXT)
- description (TEXT)
- frequency (TEXT) -- 'daily', 'weekly', 'monthly', 'yearly'
- start_date (DATE)
- end_date (DATE)
- next_occurrence (DATE)
- is_active (BOOLEAN DEFAULT TRUE)
- created_at (TIMESTAMP)

Account_Balances table:
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- account_name (TEXT)
- account_type (TEXT) -- 'checking', 'savings', 'credit', 'investment'
- balance (DECIMAL)
- updated_at (TIMESTAMP)
```

## Financial Management Features

- **Real-time balance** calculations and tracking
- **Budget monitoring** with alerts and notifications
- **Goal progress tracking** with milestone celebrations
- **Spending pattern analysis** and insights
- **Category-based organization** with custom hierarchies
- **Recurring transaction** automation and management
- **Financial forecasting** based on historical data
- **Multi-currency support** with exchange rates

## Budget and Planning Features

- **Flexible budget periods** (weekly, monthly, yearly)
- **Category-specific budgets** with spending limits
- **Budget variance analysis** and reporting
- **Automatic budget rollover** and adjustments
- **Budget alerts** and threshold notifications
- **Zero-based budgeting** support
- **Envelope budgeting** methodology
- **Budget templates** for quick setup

## Analytics and Reporting Features

- **Comprehensive financial reports** with visualizations
- **Trend analysis** and pattern recognition
- **Category spending breakdown** with comparisons
- **Income vs expense** tracking and analysis
- **Net worth calculations** and tracking
- **Savings rate monitoring** and goals
- **Cash flow projections** and forecasting
- **Custom reporting** with date ranges and filters

## Data Security and Privacy Features

- **Encrypted data storage** for sensitive information
- **Secure authentication** with password hashing
- **Data backup** and recovery capabilities
- **Privacy controls** for data sharing
- **Audit logging** for financial transactions
- **Data export** for user ownership
- **GDPR compliance** considerations
- **Financial data validation** and integrity checks

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, decimal handling, financial calculation libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Financial data validation and security
   - Budget calculation and monitoring
   - Goal tracking and progress management
   - Advanced analytics and reporting
   - Performance optimization for financial data
   - Data import/export capabilities
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all personal finance scenarios including transaction management, budget tracking, goal setting, and financial analytics with proper security and data validation.