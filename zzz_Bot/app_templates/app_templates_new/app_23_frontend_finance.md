# Frontend Generation Prompt - React Personal Finance Tracker Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, transactions, budgets, goals, reports, settings).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Personal Finance Management System Frontend**  
A modern React frontend for personal finance application, featuring intuitive financial dashboards, transaction management, budget tracking, goal setting, and comprehensive financial analytics with responsive, user-friendly design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Interactive financial dashboard with key metrics
- Comprehensive transaction management interface
- Budget creation and monitoring tools
- Financial goal setting and progress tracking
- Advanced expense categorization system
- Rich financial reports and visualizations
- Data import/export capabilities
- Responsive design with mobile optimization

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (dashboard, transactions, budgets, goals, reports, settings, auth)
  // - user authentication state
  // - transactions array with pagination
  // - budgets and budget status
  // - financial goals and progress
  // - categories and tags
  // - financial summary data
  // - selected date ranges
  // - chart and report data
  // - loading states
  // - error states

  // 4. Refs
  // - transactionFormRef
  // - budgetFormRef
  // - chartRef for visualizations
  // - fileInputRef for imports
  
  // 5. Lifecycle Functions
  // - Load user financial data on mount
  // - Setup real-time budget monitoring
  // - Initialize dashboard metrics
  // - Check authentication status
  
  // 6. Event Handlers
  // - handleTransactionAdd/Edit/Delete
  // - handleBudgetCreate/Update
  // - handleGoalCreate/Update/Contribute
  // - handleCategoryManagement
  // - handleDateRangeChange
  // - handleDataImport/Export
  // - handleReportGeneration
  // - handleAuth (login/register/logout)
  
  // 7. Financial Functions
  // - calculateTotals
  // - updateBudgetStatus
  // - trackGoalProgress
  // - generateInsights
  // - formatCurrency
  // - validateTransaction
  
  // 8. API Calls
  // - getTransactions
  // - createTransaction
  // - getBudgets/createBudget
  // - getGoals/updateGoal
  // - getReports/getAnalytics
  // - getCategories
  // - importData/exportData
  // - authenticate
  
  // 9. Utility Functions
  // - formatCurrency
  // - formatDate
  // - calculatePercentage
  // - generateChartData
  // - validateFinancialData
  // - exportToCSV
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderTransactions()
  // - renderBudgets()
  // - renderGoals()
  // - renderReports()
  // - renderSettings()
  // - renderAuthView()
  
  return (
    <main className="finance-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Financial Dashboard**
   - Account balance overview with trends
   - Monthly income vs expenses summary
   - Budget status indicators with progress bars
   - Recent transactions list
   - Financial goals progress display
   - Quick action buttons (add transaction, pay bill)
   - Spending insights and alerts
   - Net worth tracking and visualization

2. **Transaction Management**
   - Transaction list with filtering and search
   - Add/edit transaction form with validation
   - Category assignment and tagging
   - Bulk operations and import tools
   - Transaction details modal
   - Receipt attachment capability
   - Recurring transaction setup
   - Split transaction handling

3. **Budget Management**
   - Budget creation wizard with templates
   - Budget overview with spending vs limits
   - Category-wise budget breakdown
   - Budget alerts and notifications
   - Historical budget performance
   - Budget adjustment tools
   - Visual budget progress indicators
   - Budget comparison reports

4. **Financial Goals Interface**
   - Goal creation with target amounts and dates
   - Goal progress tracking with milestones
   - Contribution logging and history
   - Goal priority management
   - Achievement celebrations
   - Goal timeline visualization
   - Savings strategies and tips
   - Goal sharing and motivation features

5. **Reports and Analytics**
   - Interactive financial charts and graphs
   - Income vs expense trends over time
   - Category spending breakdown pie charts
   - Monthly/yearly financial summaries
   - Cash flow projections
   - Net worth progression tracking
   - Custom report generation
   - Export options (PDF, Excel, CSV)

6. **Settings and Profile**
   - User profile and preferences
   - Currency and localization settings
   - Category management interface
   - Account linking and management
   - Notification preferences
   - Data backup and restore
   - Privacy and security settings
   - Subscription and billing management

## Transaction Management Features

```javascript
// Advanced transaction handling:
const TransactionFeatures = {
  // - Quick transaction entry with smart categorization
  // - Bulk transaction import from bank files
  // - Transaction splitting for shared expenses
  // - Recurring transaction automation
  // - Transaction search and advanced filtering
  // - Receipt photo attachment and OCR
  // - Transaction tags and notes
  // - Duplicate transaction detection
};
```

## Budget Tracking Interface

- **Visual budget indicators** with color-coded status
- **Real-time spending tracking** against budget limits
- **Budget alerts** and overspending notifications
- **Category-wise budget allocation** with drag-and-drop
- **Budget templates** for common scenarios
- **Flexible budget periods** (weekly, monthly, yearly)
- **Budget variance analysis** with explanations
- **Automatic budget adjustments** based on income changes

## Financial Goal Management

- **Visual goal tracking** with progress bars and milestones
- **Goal prioritization** with drag-and-drop ordering
- **Automatic savings** allocation suggestions
- **Goal deadline tracking** with time-based alerts
- **Contribution scheduling** with recurring deposits
- **Goal achievement** celebrations and badges
- **Savings rate optimization** recommendations
- **Goal-based budgeting** integration

## UI/UX Requirements

- Clean, professional financial interface design
- Mobile-first responsive layout
- Fast data loading with optimistic updates
- Visual feedback for all financial operations
- Loading states for calculations and reports
- Error handling with helpful financial guidance
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for mobile transactions
- Dark/Light theme for comfortable viewing
- Data visualization with interactive charts

## Analytics and Reporting Features

```javascript
// Comprehensive financial analytics:
const AnalyticsFeatures = {
  // - Interactive charts with drill-down capabilities
  // - Spending pattern analysis and insights
  // - Income vs expense trending with forecasts
  // - Category-wise spending comparisons
  // - Net worth tracking over time
  // - Cash flow projections and planning
  // - Financial health scoring and recommendations
  // - Custom report builder with filters
};
```

## Data Visualization Components

- **Interactive charts** using modern charting libraries
- **Responsive chart design** for mobile viewing
- **Real-time data updates** with smooth animations
- **Multiple chart types** (line, bar, pie, donut, area)
- **Comparative visualizations** for period comparisons
- **Trend analysis** with predictive modeling
- **Customizable dashboards** with widget arrangements
- **Export capabilities** for presentations and sharing

## Import/Export Features

- **Bank statement import** with CSV/OFX support
- **Transaction categorization** during import
- **Duplicate detection** and merging
- **Data validation** and error reporting
- **Bulk transaction editing** after import
- **Export to multiple formats** (CSV, PDF, Excel)
- **Backup and restore** functionality
- **Data synchronization** across devices

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Transaction API functions:
// - getTransactions(filters, pagination)
// - createTransaction(transactionData)
// - updateTransaction(id, transactionData)
// - deleteTransaction(id)
// - importTransactions(fileData)

// Budget API functions:
// - getBudgets()
// - createBudget(budgetData)
// - updateBudget(id, budgetData)
// - deleteBudget(id)

// Goals API functions:
// - getGoals()
// - createGoal(goalData)
// - updateGoal(id, goalData)
// - contributeToGoal(id, amount)

// Reports API functions:
// - getFinancialSummary(dateRange)
// - getCategoryReport(dateRange)
// - getSpendingTrends(dateRange)
// - exportData(format, filters)
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
    <title>Personal Finance Tracker</title>
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
   - Include React, Vite, charting libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time financial calculations with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for financial data
   - Performance optimization (lazy loading, memoization)
   - Accessibility compliance for financial applications
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Progressive Web App features for mobile usage
   - Secure data handling and privacy protection

**Very important:** Your frontend should be feature rich, production ready, and provide excellent personal finance management experience with intuitive transaction entry, comprehensive budget tracking, effective goal management, and responsive design that works across all devices.