# Frontend Generation Prompt - React CRUD Inventory Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (dashboard, items, add/edit item, categories, alerts, reports).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**CRUD Inventory System Frontend**  
A modern React frontend for inventory management application, featuring comprehensive CRUD operations, real-time stock tracking, alert management, and analytics dashboard with intuitive, responsive design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Complete CRUD interface for inventory items
- Real-time inventory tracking and monitoring
- Category management and organization
- Stock level alerts and notifications
- Advanced search and filtering capabilities
- Analytics dashboard with charts and metrics
- Responsive design with mobile optimization
- Bulk operations for efficient management

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (dashboard, items, add-item, edit-item, categories, alerts, reports)
  // - items array with pagination
  // - currentItem for editing
  // - categories array
  // - searchQuery and filters
  // - selectedItems for bulk operations
  // - alerts array
  // - stockAlerts and notifications
  // - loading states
  // - error states
  // - dashboard metrics

  // 4. Refs
  // - itemFormRef
  // - searchInputRef
  // - bulkOperationsRef
  
  // 5. Lifecycle Functions
  // - Load items and categories on mount
  // - Setup real-time stock monitoring
  // - Initialize dashboard metrics
  
  // 6. Event Handlers
  // - handleItemCreate/Edit/Delete
  // - handleCategoryManagement
  // - handleStockAdjustment
  // - handleSearch/Filter/Sort
  // - handleBulkOperations
  // - handleAlertManagement
  // - handleNavigation
  
  // 7. CRUD Operations
  // - createItem
  // - updateItem
  // - deleteItem
  // - bulkUpdateItems
  // - adjustStock
  
  // 8. API Calls
  // - getItems
  // - getItem
  // - createItem
  // - updateItem
  // - deleteItem
  // - getCategories
  // - getAlerts
  // - getReports
  // - searchItems
  // - adjustInventory
  
  // 9. Utility Functions
  // - formatCurrency
  // - formatDate
  // - calculateStockValue
  // - generateSKU
  // - validateForm
  
  // 10. Render Methods
  // - renderDashboard()
  // - renderItemsList()
  // - renderItemForm()
  // - renderCategoriesView()
  // - renderAlertsView()
  // - renderReportsView()
  // - renderSearchFilters()
  
  return (
    <main className="inventory-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Dashboard View**
   - Key metrics overview (total items, total value, low stock count)
   - Recent activity feed
   - Stock level alerts and notifications
   - Quick action buttons (add item, adjust stock)
   - Charts and graphs for inventory analytics
   - Low stock items summary
   - Recent movements and changes

2. **Items List View**
   - Data table with sortable columns
   - Search bar with real-time filtering
   - Category filter dropdown
   - Stock status filters (in stock, low stock, out of stock)
   - Bulk selection with checkboxes
   - Pagination for large datasets
   - Add new item button
   - Export/import functionality

3. **Item Form View (Add/Edit)**
   - Item name and description fields
   - Category selection dropdown
   - Supplier selection
   - Price and cost price inputs
   - Stock quantity and minimum stock level
   - SKU field (auto-generated or manual)
   - Item image upload
   - Form validation with error display
   - Save/Cancel buttons

4. **Categories Management View**
   - Category list with item counts
   - Add/Edit/Delete category functionality
   - Hierarchical category display
   - Category description and settings
   - Drag-and-drop reordering
   - Category usage analytics

5. **Alerts and Notifications View**
   - Low stock alerts list
   - Alert severity indicators
   - Quick stock adjustment options
   - Alert history and resolution tracking
   - Bulk alert management
   - Alert configuration settings

6. **Reports and Analytics View**
   - Inventory value reports
   - Stock movement history
   - Category-wise analytics
   - Supplier performance metrics
   - Trend analysis charts
   - Export reports functionality
   - Custom date range selection

## CRUD Interface Features

```javascript
// Comprehensive CRUD operations:
const CRUDFeatures = {
  // - Inline editing for quick updates
  // - Bulk operations (delete, update, stock adjust)
  // - Duplicate item functionality
  // - Advanced validation with real-time feedback
  // - Undo/Redo for accidental changes
  // - Auto-save drafts
  // - Conflict resolution for concurrent edits
  // - Audit trail display
};
```

## Inventory Tracking Features

- **Real-time stock updates** with visual indicators
- **Stock adjustment interface** with reason tracking
- **Movement history** with detailed logs
- **Stock alerts** with configurable thresholds
- **Low stock highlighting** in item lists
- **Stock value calculations** and summaries
- **Inventory turnover** metrics and visualization

## Search and Filter Capabilities

- **Advanced search** with multiple criteria
- **Real-time filtering** as user types
- **Saved search** queries and filters
- **Quick filters** for common scenarios
- **Sort by multiple columns** with direction indicators
- **Filter combinations** (category + stock status + price range)
- **Search highlighting** in results

## UI/UX Requirements

- Clean, professional inventory management interface
- Responsive design (mobile-first approach)
- Fast data operations with optimistic updates
- Visual feedback for all user actions
- Loading states for all operations
- Error handling with user-friendly messages
- Keyboard shortcuts for power users
- Accessibility compliance (ARIA labels, keyboard navigation)
- Dark/Light theme support
- Customizable dashboard layout

## Alert System Interface

```javascript
// Alert management system:
const AlertSystem = {
  // - Real-time alert notifications
  // - Alert badges and counters
  // - Quick action buttons on alerts
  // - Alert prioritization and grouping
  // - Snooze and dismiss functionality
  // - Alert configuration interface
  // - Historical alert tracking
  // - Email notification settings
};
```

## Bulk Operations Features

- **Multi-select** with keyboard shortcuts
- **Bulk editing** for common fields
- **Bulk stock adjustments** with reason codes
- **Bulk category assignment** and updates
- **Bulk delete** with confirmation
- **Bulk export** and import operations
- **Progress tracking** for long operations

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Items API functions:
// - getItems(page, search, category, sortBy, filters)
// - getItem(id)
// - createItem(itemData)
// - updateItem(id, itemData)
// - deleteItem(id)
// - bulkUpdateItems(updates)

// Inventory API functions:
// - adjustStock(itemId, adjustment)
// - getStockMovements(itemId, dateRange)
// - getLowStockAlerts()
// - resolveAlert(alertId)

// Categories API functions:
// - getCategories()
// - createCategory(categoryData)
// - updateCategory(id, categoryData)
// - deleteCategory(id)

// Reports API functions:
// - getInventorySummary()
// - getAnalytics(dateRange)
// - searchItems(query, filters)
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
    <title>Inventory Management</title>
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
   - Real-time updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for large datasets
   - Performance optimization (virtualization, lazy loading)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Data export/import capabilities
   - Print-friendly reports and views

**Very important:** Your frontend should be feature rich, production ready, and provide excellent inventory management experience with intuitive CRUD operations, comprehensive tracking capabilities, powerful search and filtering, and responsive design that works across all devices.