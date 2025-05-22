# Frontend Generation Prompt - React Forum Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (forum home, thread view, create thread, categories, search, user profile).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Forum System Frontend**  
A modern React frontend for forum application, featuring thread browsing, discussion participation, category navigation, search functionality, and user interaction with clean, responsive design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Thread creation and viewing interface
- Nested comment system with replies
- Category navigation and filtering
- Advanced sorting and filtering options
- Search functionality with real-time suggestions
- User authentication interface
- Vote/rating system for threads and comments
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
  // - currentView (home, thread, create, categories, search, profile, auth)
  // - threads array with pagination
  // - currentThread with comments
  // - categories array
  // - searchQuery and results
  // - selectedCategory filter
  // - sortOption and filters
  // - user authentication state
  // - loading states
  // - error states

  // 4. Refs
  // - threadEditorRef
  // - commentFormRef
  // - searchInputRef
  
  // 5. Lifecycle Functions
  // - Load threads and categories on mount
  // - Check user authentication
  // - Setup real-time updates (optional)
  
  // 6. Event Handlers
  // - handleThreadCreate/Edit/Delete
  // - handleCommentAdd/Edit/Delete/Reply
  // - handleVote (threads and comments)
  // - handleCategorySelect
  // - handleSearch/Filter/Sort
  // - handleAuth (login/register/logout)
  // - handleNavigation
  
  // 7. Forum Interaction Functions
  // - voteOnThread/Comment
  // - replyToComment
  // - createThread
  // - joinDiscussion
  
  // 8. API Calls
  // - getThreads
  // - getThread
  // - createThread
  // - updateThread
  // - deleteThread
  // - getComments
  // - addComment
  // - voteContent
  // - searchForum
  // - authenticate
  
  // 9. Utility Functions
  // - formatDate
  // - formatVoteCount
  // - calculateTimeAgo
  // - highlightSearchTerms
  // - validateForm
  
  // 10. Render Methods
  // - renderForumHome()
  // - renderThreadView()
  // - renderThreadEditor()
  // - renderCategoriesView()
  // - renderSearchView()
  // - renderAuthView()
  // - renderCommentThread()
  
  return (
    <main className="forum-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Forum Home View**
   - Header with logo, search bar, and user menu
   - Category sidebar with thread counts
   - Thread list with sorting options
   - Thread preview cards with metadata
   - Pagination for thread list
   - Create new thread button (for authenticated users)
   - Pinned/featured threads section

2. **Thread View**
   - Thread title and content display
   - Author information and post metadata
   - Vote buttons with score display
   - Nested comment system
   - Reply functionality at any level
   - Comment sorting options
   - Thread actions (edit, delete, report)
   - Related threads suggestions

3. **Thread Creation/Edit View**
   - Title input field with validation
   - Rich text editor for content
   - Category selection dropdown
   - Tags input with autocomplete
   - Preview mode toggle
   - Save as draft option
   - Form validation and error display

4. **Categories View**
   - Hierarchical category display
   - Category descriptions and rules
   - Thread counts and recent activity
   - Subcategory navigation
   - Category-specific search
   - Moderator information

5. **Search Results View**
   - Advanced search form with filters
   - Search results with highlighted terms
   - Filter by content type (threads, comments)
   - Sort by relevance, date, votes
   - Search suggestions and autocomplete
   - Saved searches functionality

6. **User Authentication Views**
   - Login form with validation
   - Registration form with validation
   - User profile page with activity
   - Password reset functionality
   - User settings and preferences

## Comment System Features

```javascript
// Advanced comment system:
const CommentFeatures = {
  // - Nested threading with visual indentation
  // - Collapsible comment trees
  // - Real-time vote updates
  // - Reply notifications
  // - Comment editing with edit history
  // - Comment reporting and moderation
  // - Quote/mention functionality
  // - Comment permalinks
  // - Load more replies pagination
};
```

## Thread and Content Management

- **Rich text editing** with formatting toolbar
- **Image embedding** and file attachments
- **Thread tagging** for better organization
- **Draft saving** with auto-save functionality
- **Content preview** before posting
- **Edit history** tracking for transparency
- **Content reporting** and moderation tools
- **Thread watching** and notifications

## Search and Navigation Features

- **Real-time search** with instant results
- **Advanced search operators** (AND, OR, NOT, quotes)
- **Search within categories** and date ranges
- **Search highlighting** in results
- **Auto-complete** for search terms
- **Search history** and saved searches
- **Breadcrumb navigation** for deep threads
- **Keyboard navigation** support

## UI/UX Requirements

- Clean, modern forum interface design
- Responsive layout (mobile-first approach)
- Fast thread and comment loading
- Smooth navigation between views
- Visual feedback for all user interactions
- Loading states for all operations
- Error handling with user-friendly messages
- Accessibility compliance (ARIA labels, keyboard navigation)
- Dark/Light theme support
- Customizable interface preferences

## Voting and Interaction Features

```javascript
// User interaction system:
const InteractionFeatures = {
  // - Upvote/downvote with visual feedback
  // - Vote count animations
  // - Prevent multiple votes per user
  // - Reputation system display
  // - User badges and achievements
  // - Thread/comment bookmarking
  // - Follow/unfollow threads
  // - User mention system (@username)
};
```

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Thread API functions:
// - getThreads(page, category, sort, filter)
// - getThread(id)
// - createThread(threadData)
// - updateThread(id, threadData)
// - deleteThread(id)
// - voteOnThread(id, voteType)

// Comment API functions:
// - getComments(threadId)
// - addComment(threadId, commentData)
// - replyToComment(commentId, replyData)
// - updateComment(id, commentData)
// - deleteComment(id)
// - voteOnComment(id, voteType)

// Category and Search API functions:
// - getCategories()
// - searchForum(query, filters)
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
    <title>Forum Application</title>
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
   - Include React, Vite, rich text editor libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time updates for dynamic content
   - Responsive design with mobile optimization
   - Proper state management for complex forum data
   - Performance optimization (lazy loading, virtualization)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - SEO optimization for thread content
   - Social sharing capabilities

**Very important:** Your frontend should be feature rich, production ready, and provide excellent forum experience with intuitive thread browsing, engaging discussion interface, powerful search capabilities, and responsive design that works across all devices.