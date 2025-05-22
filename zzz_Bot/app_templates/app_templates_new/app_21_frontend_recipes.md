# Frontend Generation Prompt - React Recipe Management Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (recipes, create, meal-plans, timers, shopping, settings).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Recipe Management System Frontend**  
A modern React frontend for recipe management application, featuring intuitive recipe creation, meal planning, cooking timers, nutrition tracking, and collaborative recipe sharing with beautiful, kitchen-friendly design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Recipe creation and editing with rich media support
- Comprehensive ingredient tracking and management
- Visual meal planning with calendar integration
- Interactive cooking timers with notifications
- Nutrition information display and analysis
- Advanced recipe search and filtering
- Shopping list generation and management
- Mobile-responsive design for kitchen use

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (recipes, create, meal-plans, timers, shopping, nutrition, auth)
  // - recipes array with filtering and search
  // - currentRecipe for viewing/editing
  // - mealPlans with calendar data
  // - activeTimers with countdown states
  // - ingredients database for autocomplete
  // - shoppingList with checked items
  // - user authentication state
  // - dietary preferences and restrictions
  // - nutrition data and goals
  // - loading states
  // - error states

  // 4. Refs
  // - recipeFormRef
  // - timerRefs for multiple timers
  // - mealPlanCalendarRef
  // - ingredientSearchRef
  
  // 5. Lifecycle Functions
  // - Load recipes and user preferences
  // - Check user authentication
  // - Initialize cooking timers
  // - Setup notification permissions
  
  // 6. Event Handlers
  // - handleRecipeCreate/Edit/Delete
  // - handleMealPlanAdd/Remove/Update
  // - handleTimerStart/Stop/Pause
  // - handleIngredientAdd/Remove
  // - handleShoppingListUpdate
  // - handleAuth (login/register/logout)
  // - handleSearch/Filter
  
  // 7. Recipe Management Functions
  // - createRecipe
  // - calculateNutrition
  // - scaleRecipe
  // - addToMealPlan
  // - generateShoppingList
  
  // 8. API Calls
  // - getRecipes
  // - createRecipe
  // - updateRecipe
  // - getMealPlans
  // - createMealPlan
  // - getIngredients
  // - createTimer
  // - getShoppingList
  // - authenticate
  
  // 9. Utility Functions
  // - formatTime
  // - convertUnits
  // - calculateServings
  // - formatNutrition
  // - validateRecipe
  
  // 10. Render Methods
  // - renderRecipesList()
  // - renderRecipeEditor()
  // - renderMealPlanCalendar()
  // - renderCookingTimers()
  // - renderShoppingList()
  // - renderNutritionInfo()
  // - renderAuthView()
  
  return (
    <main className="recipe-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Recipe Library and Discovery**
   - Grid/list view of recipes with photos
   - Advanced search with multiple filters
   - Recipe categories and cuisine types
   - Favorite recipes and personal collections
   - Recipe ratings and reviews display
   - Quick action buttons (cook, plan, share)
   - Recently viewed and recommended recipes

2. **Recipe Creation and Editing**
   - Rich text editor for recipe instructions
   - Dynamic ingredient list with unit conversion
   - Photo upload with crop and resize tools
   - Nutrition calculation with real-time updates
   - Recipe timing and difficulty settings
   - Step-by-step instruction builder
   - Recipe testing and notes section
   - Publication and sharing controls

3. **Meal Planning Calendar**
   - Weekly/monthly calendar view
   - Drag-and-drop recipe scheduling
   - Meal type organization (breakfast, lunch, dinner)
   - Nutrition tracking across planned meals
   - Leftover management and suggestions
   - Grocery list integration
   - Meal prep batch planning
   - Dietary goal monitoring

4. **Cooking Timers and Assistant**
   - Multiple concurrent timer management
   - Visual and audio timer notifications
   - Step-by-step cooking guidance
   - Recipe scaling with automatic adjustments
   - Temperature and doneness reminders
   - Cooking technique tips and videos
   - Emergency timer controls
   - Timer history and cooking logs

5. **Shopping List and Inventory**
   - Auto-generated shopping lists from meal plans
   - Manual item addition with categories
   - Quantity consolidation and optimization
   - Store layout optimization and sorting
   - Price tracking and budget management
   - Pantry inventory and expiration tracking
   - Barcode scanning for quick addition
   - Shared shopping lists for families

6. **Nutrition and Dietary Analysis**
   - Detailed nutrition breakdown per recipe
   - Daily/weekly nutrition summaries
   - Dietary restriction compliance checking
   - Allergen identification and warnings
   - Nutrition goal setting and tracking
   - Macro/micronutrient visualization
   - Meal nutrition comparison tools
   - Custom dietary preference management

## Recipe Management Features

```javascript
// Advanced recipe functionality:
const RecipeFeatures = {
  // - Rich text editing with formatting options
  // - Ingredient autocomplete with nutrition data
  // - Recipe scaling with proportional adjustments
  // - Nutrition calculation in real-time
  // - Photo upload with editing capabilities
  // - Recipe versioning and change tracking
  // - Collaborative recipe editing
  // - Recipe import from URLs and PDFs
};
```

## Meal Planning Interface

- **Visual calendar** with drag-and-drop scheduling
- **Nutrition tracking** across planned meals
- **Leftover integration** with recipe suggestions
- **Batch cooking** planning and prep guides
- **Shopping list generation** from meal plans
- **Dietary goal monitoring** with progress indicators
- **Meal prep templates** for efficient planning
- **Family meal coordination** with preferences

## Cooking Timer System

- **Multiple timer management** with visual indicators
- **Recipe integration** with step-by-step timing
- **Audio and visual notifications** with customization
- **Timer templates** for common cooking tasks
- **Emergency controls** for quick timer management
- **Timer history** and cooking session tracking
- **Smart notifications** based on cooking stage
- **Voice control** integration for hands-free use

## UI/UX Requirements

- Clean, kitchen-friendly interface design
- Mobile-first responsive layout
- Touch-friendly controls for cooking environments
- High contrast mode for kitchen lighting
- Large, easy-to-read text and buttons
- Spill-resistant interface design
- Visual feedback for all cooking actions
- Loading states for recipe operations
- Error handling with helpful cooking tips
- Accessibility compliance for all users
- Dark/Light theme for different environments

## Shopping and Inventory Features

```javascript
// Shopping and inventory management:
const ShoppingFeatures = {
  // - Smart shopping list generation from meal plans
  // - Ingredient consolidation and optimization
  // - Store layout integration for efficient shopping
  // - Price tracking and budget management
  // - Pantry inventory with expiration tracking
  // - Barcode scanning for quick item addition
  // - Shared lists for family coordination
  // - Automatic reordering for staple items
};
```

## Nutrition Tracking Interface

- **Real-time nutrition calculation** during recipe creation
- **Visual nutrition displays** with charts and graphs
- **Dietary goal tracking** with progress indicators
- **Allergen warnings** and dietary restriction compliance
- **Nutrition comparison** between recipes and meals
- **Daily/weekly summaries** with trend analysis
- **Custom nutrition targets** for different diets
- **Meal nutrition optimization** suggestions

## Search and Discovery Interface

- **Advanced search** with multiple filter criteria
- **Ingredient-based search** for available items
- **Dietary restriction filtering** with compliance checking
- **Cooking time and difficulty** filtering options
- **Cuisine and category** browsing with recommendations
- **Seasonal recipe** suggestions and trending dishes
- **Personal recommendation** engine based on preferences
- **Social discovery** with community recipes

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData, dietaryPreferences)
// - logout()
// - getCurrentUser()

// Recipe API functions:
// - getRecipes(filters, search, pagination)
// - getRecipe(id)
// - createRecipe(recipeData)
// - updateRecipe(id, recipeData)
// - deleteRecipe(id)
// - scaleRecipe(id, servings)

// Meal Planning API functions:
// - getMealPlans(dateRange)
// - createMealPlan(mealData)
// - updateMealPlan(id, mealData)
// - deleteMealPlan(id)

// Timer API functions:
// - createTimer(timerData)
// - getActiveTimers()
// - updateTimer(id, action)
// - deleteTimer(id)

// Shopping API functions:
// - getShoppingList(dateRange)
// - updateShoppingList(items)
// - getIngredients(search)

// Nutrition API functions:
// - getNutritionInfo(recipeId)
// - calculateMealNutrition(mealPlanId)
// - getDietaryAnalysis(dateRange)
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
    <title>Recipe Manager</title>
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
   - Include React, Vite, rich text editor, calendar libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Offline recipe access with data caching
   - Responsive design with mobile optimization
   - Proper state management for recipe data
   - Performance optimization (lazy loading, image optimization)
   - Accessibility compliance for kitchen environments
   - Clean code with comments
   - User experience enhancements (intuitive flows, cooking-friendly design)
   - Progressive Web App features
   - Push notifications for timers and meal reminders

**Very important:** Your frontend should be feature rich, production ready, and provide excellent recipe management experience with intuitive recipe creation, comprehensive meal planning, effective cooking assistance, and responsive design optimized for kitchen and mobile use.