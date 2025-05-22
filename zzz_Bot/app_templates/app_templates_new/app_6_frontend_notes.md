# Frontend Generation Prompt - React Notes Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (notes list, note editor, categories, search, archived).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Notes System Frontend**  
A modern React frontend for notes application, featuring intuitive note creation/editing, categorization, search functionality, and archive management with clean, responsive design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Note creation and editing with rich text support
- Note listing and viewing with multiple layout options
- Category management and organization
- Full-text search with real-time suggestions
- Note archiving and restoration
- Auto-save functionality
- Responsive design
- Keyboard shortcuts and accessibility

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (list, editor, categories, search, archived)
  // - notes array with pagination
  // - currentNote for editing
  // - categories array
  // - selectedCategory filter
  // - searchQuery and results
  // - tags array
  // - loading states
  // - error states
  // - auto-save status

  // 4. Refs
  // - editorRef for focus management
  // - searchInputRef
  // - autoSaveTimeoutRef
  
  // 5. Lifecycle Functions
  // - Load notes and categories on mount
  // - Setup auto-save functionality
  // - Setup keyboard shortcuts
  
  // 6. Event Handlers
  // - handleNoteCreate/Edit/Delete
  // - handleNoteSelect
  // - handleCategoryChange
  // - handleSearch
  // - handleArchive/Restore
  // - handleAutoSave
  // - handleKeyboardShortcuts
  
  // 7. Auto-save and Content Management
  // - setupAutoSave
  // - saveNote
  // - discardChanges
  // - trackUnsavedChanges
  
  // 8. API Calls
  // - getNotes
  // - getNote
  // - createNote
  // - updateNote
  // - deleteNote
  // - searchNotes
  // - getCategories
  // - archiveNote
  // - autoSaveNote
  
  // 9. Utility Functions
  // - formatDate
  // - truncateText
  // - highlightSearchTerms
  // - generateNotePreview
  
  // 10. Render Methods
  // - renderNotesList()
  // - renderNoteEditor()
  // - renderCategoriesView()
  // - renderSearchView()
  // - renderArchivedView()
  // - renderSidebar()
  
  return (
    <main className="notes-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Notes List View**
   - Sidebar with categories and navigation
   - Notes grid/list with multiple layout options
   - Note preview cards with title, content preview, date
   - Search bar with real-time filtering
   - Create new note button
   - Sort options (date, title, category)
   - Bulk operations (archive, delete selected)

2. **Note Editor View**
   - Full-screen or split-pane editing interface
   - Rich text editor with formatting toolbar
   - Title and content editing areas
   - Category selection dropdown
   - Tags input with autocomplete
   - Auto-save indicator and status
   - Save/Cancel/Delete buttons
   - Character/word count display

3. **Categories Management View**
   - List of all categories with note counts
   - Create/Edit/Delete category functionality
   - Color picker for category styling
   - Category description editing
   - Drag-and-drop reordering
   - Category usage statistics

4. **Search Results View**
   - Search input with advanced options
   - Filtered results with highlighted search terms
   - Search suggestions and autocomplete
   - Filter by category, date range, tags
   - Search history and saved searches
   - Export search results option

5. **Archived Notes View**
   - List of archived notes
   - Restore functionality for archived notes
   - Permanent delete option
   - Bulk restore operations
   - Archive date and metadata display

6. **Navigation and UI Components**
   - Responsive sidebar navigation
   - Top toolbar with actions
   - Breadcrumb navigation
   - Modal dialogs for confirmations
   - Toast notifications for actions
   - Loading spinners and states

## Note Editor Features

```javascript
// Rich text editing capabilities:
const EditorFeatures = {
  // - Bold, italic, underline formatting
  // - Bullet and numbered lists
  // - Headers and text styles
  // - Link insertion and editing
  // - Code blocks and inline code
  // - Auto-save with visual indicators
  // - Undo/Redo functionality
  // - Full-screen editing mode
  // - Word/character count
  // - Find and replace
};
```

## Auto-Save and Data Management

- **Auto-save** with configurable intervals (e.g., every 30 seconds)
- **Conflict resolution** for simultaneous edits
- **Unsaved changes** warning before navigation
- **Draft management** for new notes
- **Version history** with restore points
- **Offline support** with local storage backup
- **Data export** and import functionality

## Search and Filter Features

- **Real-time search** as user types
- **Search highlighting** in results
- **Advanced search** with operators (AND, OR, NOT)
- **Filter combinations** (category + date + tags)
- **Search suggestions** based on note content
- **Recent searches** history
- **Saved search** queries

## UI/UX Requirements

- Clean, distraction-free writing interface
- Responsive design (mobile-first approach)
- Fast note switching and loading
- Smooth animations and transitions
- Keyboard shortcuts for common actions
- Accessibility compliance (ARIA labels, keyboard navigation)
- Dark/Light theme support
- Customizable layout options (grid, list, compact)
- Visual feedback for all user actions

## Keyboard Shortcuts

```javascript
// Essential keyboard shortcuts:
const KeyboardShortcuts = {
  'Ctrl+N': 'Create new note',
  'Ctrl+S': 'Save current note', 
  'Ctrl+F': 'Focus search',
  'Ctrl+E': 'Edit selected note',
  'Ctrl+D': 'Delete selected note',
  'Ctrl+A': 'Archive selected note',
  'Esc': 'Close editor/Cancel',
  'Ctrl+Z': 'Undo',
  'Ctrl+Y': 'Redo'
};
```

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Notes API functions:
// - getNotes(page, category, search, archived)
// - getNote(id)
// - createNote(noteData)
// - updateNote(id, noteData)
// - deleteNote(id)
// - archiveNote(id)
// - restoreNote(id)
// - autoSaveNote(id, content)

// Categories API functions:
// - getCategories()
// - createCategory(categoryData)
// - updateCategory(id, categoryData)
// - deleteCategory(id)

// Search API functions:
// - searchNotes(query, filters)
// - getTags()
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
    <title>Notes Application</title>
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
   - Auto-save with conflict resolution
   - Responsive design with mobile optimization
   - Proper state management for large note collections
   - Performance optimization (virtualization, lazy loading)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Offline functionality with local storage

**Very important:** Your frontend should be feature rich, production ready, and provide excellent note-taking experience with intuitive editing, powerful search, efficient organization, and responsive design that works across all devices.