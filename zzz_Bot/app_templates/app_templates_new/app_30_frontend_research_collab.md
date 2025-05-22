# Frontend Generation Prompt - React Recipe Management Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (recipes, meal-plans, cooking, favorites, profile, auth).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Recipe Management System Frontend**  
A modern React frontend for recipe management application, featuring intuitive recipe creation, comprehensive meal planning, interactive cooking assistance, nutrition tracking, and social sharing with responsive, user-friendly design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Comprehensive recipe creation and editing interface
- Visual ingredient tracking and management
- Interactive meal planning calendar
- Recipe categorization and organization tools
- Nutrition information display and tracking
- Interactive cooking timer and step guidance
- Recipe sharing and social features
- Shopping list generation and management
- Advanced search and filtering capabilities
- Mobile-responsive cooking interface

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (recipes, meal-plans, cooking, favorites, profile, auth)
  // - recipes array with filtering and pagination
  // - currentRecipe for detailed view/editing
  // - ingredients database and selected ingredients
  // - meal plans and calendar data
  // - cooking timers and active cooking session
  // - favorites and user preferences
  // - search query and filters
  // - nutrition data and tracking
  // - user authentication state
  // - loading states
  // - error states

  // 4. Refs
  // - recipeFormRef
  // - ingredientSearchRef
  // - mealPlanCalendarRef
  // - cookingTimerRef
  
  // 5. Lifecycle Functions
  // - Load recipes and user data on mount
  // - Setup cooking timers and notifications
  // - Initialize meal planning calendar
  // - Check user authentication
  
  // 6. Event Handlers
  // - handleRecipeCreate/Edit/Delete
  // - handleIngredientAdd/Remove/Update
  // - handleMealPlanCreate/Update
  // - handleCookingStart/Timer
  // - handleSearch/Filter
  // - handleFavorite/Share
  // - handleAuth (login/register/logout)
  // - handleNutritionTracking
  
  // 7. Recipe Management Functions
  // - createRecipe
  // - updateRecipe
  // - scaleRecipe
  // - calculateNutrition
  // - generateShoppingList
  
  // 8. API Calls
  // - getRecipes
  // - createRecipe
  // - updateRecipe
  // - getIngredients
  // - getMealPlans
  // - createMealPlan
  // - searchRecipes
  // - manageTimers
  // - authenticate
  
  // 9. Utility Functions
  // - formatTime/duration
  // - calculateNutrition
  // - formatQuantity
  // - validateRecipe
  // - convertUnits
  
  // 10. Render Methods
  // - renderRecipesList()
  // - renderRecipeDetail()
  // - renderRecipeEditor()
  // - renderMealPlanner()
  // - renderCookingInterface()
  // - renderFavorites()
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

1. **Recipe Collection View**
   - Recipe cards with images and quick info
   - Grid and list view toggle
   - Advanced search and filtering interface
   - Category-based navigation
   - Sort options (newest, popular, rating, time)
   - Create new recipe button
   - Bulk operations for recipe management

2. **Recipe Detail and Editing View**
   - Full recipe display with images
   - Ingredient list with quantities and units
   - Step-by-step instructions with images
   - Nutrition information panel
   - Recipe scaling calculator
   - Edit mode with form validation
   - Recipe sharing and social features
   - Related recipes suggestions

3. **Meal Planning Interface**
   - Interactive calendar view
   - Drag-and-drop recipe assignment
   - Meal type organization (breakfast, lunch, dinner)
   - Weekly and monthly planning views
   - Shopping list generation
   - Nutrition summary for planned meals
   - Meal prep scheduling and reminders

4. **Cooking Assistant Interface**
   - Step-by-step cooking guidance
   - Interactive cooking timers
   - Ingredient checklist with checkboxes
   - Cooking tips and techniques
   - Temperature and timing guidance
   - Voice commands and hands-free operation
   - Progress tracking through recipe steps

5. **Ingredient and Pantry Management**
   - Ingredient database with search
   - Pantry inventory tracking
   - Expiration date reminders
   - Shopping list management
   - Ingredient substitution suggestions
   - Nutrition information for ingredients
   - Bulk ingredient operations

6. **User Profile and Preferences**
   - User dashboard with statistics
   - Dietary preferences and restrictions
   - Favorite recipes collection
   - Recipe creation history
   - Nutrition goals and tracking
   - Account settings and preferences

## Recipe Creation and Editing Features

```javascript
// Advanced recipe editor:
const RecipeEditorFeatures = {
  // - Rich text editor for instructions with formatting
  // - Drag-and-drop ingredient ordering
  // - Image upload with cropping and optimization
  // - Automatic nutrition calculation
  // - Recipe scaling with unit conversion
  // - Template selection for common recipe types
  // - Auto-save functionality with draft management
  // - Ingredient substitution suggestions
};
```

## Meal Planning Features

- **Interactive calendar** with drag-and-drop meal assignment
- **Automated shopping lists** from selected recipes
- **Nutrition tracking** across planned meals
- **Meal prep scheduling** with time estimates
- **Recipe suggestions** based on dietary goals
- **Leftover tracking** and recipe recommendations
- **Batch cooking** planning and optimization
- **Weekly/monthly** meal planning templates

## Cooking Assistant Interface

- **Step-by-step guidance** with visual progress
- **Multiple timer management** for complex recipes
- **Hands-free operation** with voice commands
- **Ingredient prep checklist** with checkmarks
- **Cooking techniques** and tips integration
- **Temperature monitoring** and alerts
- **Recipe scaling** during cooking
- **Emergency substitutions** and adjustments

## UI/UX Requirements

- Clean, modern recipe interface design
- Mobile-first responsive layout for kitchen use
- Fast recipe browsing and search
- Visual feedback for all cooking actions
- Loading states for all operations
- Error handling with helpful cooking tips
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for tablet cooking
- Smooth animations and transitions
- Offline recipe access for cooking

## Nutrition and Health Interface

```javascript
// Comprehensive nutrition tracking:
const NutritionFeatures = {
  // - Visual nutrition charts and breakdowns
  // - Daily nutrition goal tracking
  // - Macro and micronutrient analysis
  // - Allergen identification and warnings
  // - Dietary restriction filtering
  // - Calorie counting with meal planning
  // - Health goal integration and progress
  // - Nutritional comparison between recipes
};
```

## Search and Discovery Features

- **Advanced search** with ingredient-based queries
- **Visual filters** for dietary restrictions and preferences
- **Recipe recommendations** based on cooking history
- **Trending recipes** and popular content
- **Seasonal ingredient** suggestions
- **Cuisine-based browsing** with cultural context
- **Difficulty-based filtering** for skill level
- **Time-based search** for quick meal solutions

## Social and Sharing Features

- **Recipe sharing** with friends and family
- **Recipe collections** and collaborative cookbooks
- **Rating and review** system for recipes
- **Cooking photos** and meal sharing
- **Recipe comments** and cooking tips exchange
- **Follow favorite** recipe creators
- **Recipe challenges** and cooking goals
- **Community features** for recipe discovery

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Recipe API functions:
// - getRecipes(filters, sort, page)
// - getRecipe(id)
// - createRecipe(recipeData)
// - updateRecipe(id, recipeData)
// - deleteRecipe(id)
// - scaleRecipe(id, servings)
// - favoriteRecipe(id)

// Ingredient API functions:
// - getIngredients(search)
// - addIngredient(ingredientData)
// - updateIngredient(id, ingredientData)

// Meal Planning API functions:
// - getMealPlans(dateRange)
// - createMealPlan(mealPlanData)
// - updateMealPlan(id, mealPlanData)
// - generateShoppingList(mealPlanId)

// Cooking API functions:
// - getTimers()
// - createTimer(timerData)
// - updateTimer(id, timerData)
// - deleteTimer(id)

// Search API functions:
// - searchRecipes(query, filters)
// - getCategories()
// - getFavorites()
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
    <title>Recipe Management</title>
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
   - Include React, Vite, calendar libraries, timer components, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for recipe data
   - Performance optimization (lazy loading, memoization)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Offline functionality with cached recipes
   - Progressive Web App features for kitchen use

**Very important:** Your frontend should be feature rich, production ready, and provide excellent recipe management experience with intuitive recipe creation, comprehensive meal planning, interactive cooking assistance, and responsive design that works across all devices, especially optimized for kitchen and mobile use.