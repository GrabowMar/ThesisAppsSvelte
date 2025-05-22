# Frontend Generation Prompt - React Feedback Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (feedback form, success page, admin panel).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Feedback System Frontend**  
A modern React frontend for feedback collection application, featuring comprehensive forms, validation, success notifications, and optional admin interface with clean, responsive UI.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Multi-field feedback form
- Client-side form validation
- Submission handling with loading states
- Success/error notifications
- Form reset functionality
- Responsive design
- Optional admin dashboard view

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (form, success, admin)
  // - formData (name, email, category, subject, message, rating)
  // - categories array
  // - validation errors
  // - loading states
  // - submission status
  // - feedback list (for admin)

  // 4. Lifecycle Functions
  // - Load categories on mount
  // - Initialize form state
  
  // 5. Event Handlers
  // - handleInputChange
  // - handleSubmit
  // - handleReset
  // - handleViewChange
  // - handleValidation
  
  // 6. Validation Functions
  // - validateEmail
  // - validateRequired
  // - validateLength
  // - validateForm
  
  // 7. API Calls
  // - submitFeedback
  // - getCategories
  // - getFeedbackList (admin)
  // - getAnalytics (admin)
  
  // 8. Render Methods
  // - renderFeedbackForm()
  // - renderSuccessPage()
  // - renderAdminPanel()
  // - renderFormField()
  // - renderValidationError()
  
  return (
    <main className="feedback-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 9. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Feedback Form View**
   - Name input field (required)
   - Email input field (required, with validation)
   - Category dropdown (required, populated from API)
   - Subject input field (required)
   - Message textarea (required, character count)
   - Rating input (optional, 1-5 stars or select)
   - Submit button with loading state
   - Reset/Clear button
   - Real-time validation feedback
   - Error display for each field

2. **Success Page View**
   - Success message with submission ID
   - Thank you message
   - Submit another feedback button
   - Back to home navigation
   - Optional feedback summary

3. **Admin Panel View (Optional)**
   - Feedback submissions list
   - Search and filter functionality
   - Analytics dashboard
   - Category management
   - Export functionality

4. **Form Components**
   - Input field wrapper with validation
   - Dropdown with search capability
   - Star rating component
   - Character counter for textarea
   - Loading spinner component
   - Success/error notification banner

## Form Validation Rules

```javascript
// Client-side validation:
const validationRules = {
  name: {
    required: true,
    minLength: 2,
    maxLength: 50,
    pattern: /^[a-zA-Z\s]+$/
  },
  email: {
    required: true,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  },
  category: {
    required: true
  },
  subject: {
    required: true,
    minLength: 5,
    maxLength: 100
  },
  message: {
    required: true,
    minLength: 10,
    maxLength: 1000
  },
  rating: {
    min: 1,
    max: 5
  }
};
```

## UI/UX Requirements

- Clean, modern form design
- Progressive form validation (validate on blur/change)
- Visual feedback for validation states
- Responsive layout (mobile-friendly)
- Loading states during submission
- Success animations
- Error message styling
- Character counters for text fields
- Required field indicators
- Accessible form labels and ARIA attributes

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// API functions:
// - submitFeedback(formData)
// - getCategories()
// - getFeedbackList(filters, pagination)
// - getAnalytics()
// - createCategory(categoryData)
// - deleteFeedback(id)
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
    <title>Feedback Form</title>
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
   - Include React, Vite, and any additional libraries needed for form handling

3. **Production Ready Features**
   - Comprehensive form validation
   - Error boundaries and fallbacks
   - Loading states for all operations
   - Responsive design with mobile optimization
   - Proper state management
   - Form persistence (save draft)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (auto-save, confirmation dialogs)

**Very important:** Your frontend should be feature rich, production ready, and provide excellent user experience with intuitive form design, clear validation feedback, and smooth submission flow.