# Frontend Generation Prompt - React Blog Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (home, post details, create/edit, login/register, profile).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Blog System Frontend**  
A modern React frontend for blog application, featuring user authentication, content creation/editing, comment system, and responsive design with markdown support.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- User authentication interface (login/register)
- Blog post creation and editing with markdown support
- Comment system with nested replies
- Post categorization and filtering
- Search functionality
- Responsive design
- User profile management

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (home, post, create, edit, login, register, profile)
  // - user authentication state
  // - posts array with pagination
  // - currentPost details
  // - comments array
  // - categories array
  // - search state
  // - loading states
  // - error states

  // 4. Refs
  // - markdownEditorRef
  // - commentFormRef
  
  // 5. Lifecycle Functions
  // - Check authentication on mount
  // - Load posts and categories
  // - Setup markdown editor
  
  // 6. Event Handlers
  // - handleLogin/Register/Logout
  // - handlePostCreate/Edit/Delete
  // - handleCommentAdd/Edit/Delete
  // - handleSearch
  // - handleCategoryFilter
  // - handleNavigation
  
  // 7. API Calls
  // - authentication functions
  // - post CRUD operations
  // - comment operations
  // - category management
  // - search functionality
  
  // 8. Utility Functions
  // - formatDate
  // - truncateText
  // - renderMarkdown
  // - validateForm
  
  // 9. Render Methods
  // - renderHome()
  // - renderPost()
  // - renderPostEditor()
  // - renderAuth()
  // - renderProfile()
  // - renderComments()
  // - renderNavigation()
  
  return (
    <main className="blog-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 10. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Home/Blog List View**
   - Header with navigation and search
   - Post list with pagination
   - Category sidebar/filter
   - Featured posts section
   - User authentication status
   - Create post button (for authenticated users)

2. **Post Detail View**
   - Full post content with markdown rendering
   - Author information and metadata
   - Category and tags display
   - Comment section with nested replies
   - Edit/Delete buttons (for post author)
   - Social sharing buttons
   - Related posts suggestions

3. **Post Editor View (Create/Edit)**
   - Title input field
   - Category dropdown
   - Tags input with autocomplete
   - Markdown editor with preview
   - Save as draft/Publish options
   - Image upload capability
   - Form validation and auto-save

4. **Authentication Views**
   - Login form with validation
   - Registration form with validation
   - Password strength indicator
   - Remember me option
   - Forgot password link

5. **User Profile View**
   - User information display/edit
   - User's posts list
   - Account settings
   - Change password form

6. **Navigation Components**
   - Header with logo and navigation links
   - User menu dropdown
   - Search bar with suggestions
   - Mobile-responsive menu

## Comment System Features

```javascript
// Comment component structure:
const CommentComponent = {
  // - Display comment content
  // - Author info and timestamp
  // - Reply button and form
  // - Edit/Delete for comment author
  // - Nested comment threading
  // - Load more replies pagination
  // - Real-time comment updates
};
```

## Markdown Editor Features

- **Live preview** split-pane or toggle view
- **Toolbar** with formatting buttons
- **Syntax highlighting** for code blocks
- **Auto-save** functionality
- **Image upload** with drag-and-drop
- **Table editor** support
- **Link insertion** helper
- **Keyboard shortcuts** for common formatting

## UI/UX Requirements

- Clean, modern blog design
- Responsive layout (mobile-first)
- Fast navigation between views
- Loading states for all operations
- Error handling with user feedback
- Infinite scroll or pagination for posts
- Search with real-time suggestions
- Dark/Light theme support (optional)
- Accessibility compliance (ARIA labels, keyboard navigation)
- SEO-friendly structure

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Blog API functions:
// - getPosts(page, category, search)
// - getPost(id)
// - createPost(postData)
// - updatePost(id, postData)
// - deletePost(id)

// Comment API functions:
// - getComments(postId)
// - addComment(postId, commentData)
// - updateComment(id, commentData)
// - deleteComment(id)

// Category API functions:
// - getCategories()
// - searchPosts(query)
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
    <title>Blog Application</title>
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
   - Include React, Vite, markdown parsing library, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive form validation
   - Error boundaries and fallbacks
   - Loading states for all operations
   - Responsive design with mobile optimization
   - Proper state management
   - Content persistence and auto-save
   - SEO optimization
   - Accessibility compliance
   - Clean code with comments
   - Performance optimization (lazy loading, memoization)

**Very important:** Your frontend should be feature rich, production ready, and provide excellent user experience with intuitive navigation, smooth content creation/editing, efficient comment system, and responsive design that works across all devices.