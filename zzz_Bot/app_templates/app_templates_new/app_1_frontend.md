# Frontend Generation Prompt - React Login/Register Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (login, register, dashboard).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Authentication System Frontend**  
A modern React frontend for user authentication system, featuring user registration and login capabilities with clean, responsive UI.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- User registration form
- Login form
- Dashboard view (protected)
- Form validation
- Loading states
- Error handling and display
- Responsive design

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (login, register, dashboard)
  // - user authentication state
  // - form data
  // - loading states
  // - error messages

  // 4. Lifecycle Functions
  // - Check authentication on mount
  
  // 5. Event Handlers
  // - handleLogin
  // - handleRegister
  // - handleLogout
  // - handleViewChange
  
  // 6. API Calls
  // - login API call
  // - register API call
  // - logout API call
  // - get user info
  
  // 7. Render Methods
  // - renderLogin()
  // - renderRegister()
  // - renderDashboard()
  
  return (
    <main className="app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 8. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Login View**
   - Username/email input field
   - Password input field
   - Login button
   - Link to switch to register view
   - Error display
   - Loading state

2. **Register View**
   - Username input field
   - Email input field
   - Password input field
   - Confirm password field
   - Register button
   - Link to switch to login view
   - Error display
   - Loading state

3. **Dashboard View**
   - Welcome message with user info
   - Logout button
   - Protected content
   - Navigation elements

4. **Navigation/Routing**
   - Conditional rendering based on authentication state
   - View switching without page reload
   - URL-friendly routing (optional enhancement)

## UI/UX Requirements

- Clean, modern design
- Responsive layout (mobile-friendly)
- Form validation feedback
- Loading indicators
- Error message display
- Smooth transitions between views
- Accessibility considerations

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// API functions:
// - loginUser(credentials)
// - registerUser(userData) 
// - logoutUser()
// - getCurrentUser()
// - getDashboardData()
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
    <title>Login/Register App</title>
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
   - Include React, Vite, and any additional libraries needed

3. **Production Ready Features**
   - Form validation
   - Error boundaries
   - Loading states
   - Responsive design
   - Proper state management
   - Clean code with comments

**Very important:** Your frontend should be feature rich, production ready, and provide excellent user experience with proper error handling and validation.