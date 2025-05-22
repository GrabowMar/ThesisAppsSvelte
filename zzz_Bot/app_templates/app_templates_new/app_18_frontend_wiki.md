# Frontend Generation Prompt - React Wiki Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (home, page view, edit, history, search, categories).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Wiki System Frontend**  
A modern React frontend for wiki platform, featuring intuitive page editing, content organization, version history, collaborative features, and comprehensive search with clean, knowledge-focused design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Rich markdown editor with live preview
- Hierarchical content organization and navigation
- Advanced search with filtering and highlighting
- Version history with diff visualization
- Collaborative editing with conflict resolution
- Page linking and cross-references
- File attachment and media management
- Mobile-responsive design for reading and editing

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (home, page, edit, history, search, categories, auth)
  // - currentPage with content and metadata
  // - pages array for navigation
  // - searchResults and query state
  // - editingContent and preview mode
  // - versionHistory and selected revisions
  // - user authentication state
  // - categories and tags arrays
  // - navigation breadcrumbs
  // - loading states
  // - error states

  // 4. Refs
  // - markdownEditorRef
  // - previewRef
  // - searchInputRef
  // - scrollPositionRef
  
  // 5. Lifecycle Functions
  // - Load initial page and navigation
  // - Check user authentication
  // - Setup keyboard shortcuts
  // - Initialize markdown editor
  
  // 6. Event Handlers
  // - handlePageEdit/Save/Cancel
  // - handleSearch/Filter
  // - handlePageNavigation
  // - handleVersionCompare/Revert
  // - handleLinkClick/Creation
  // - handleAuth (login/register/logout)
  // - handleFileUpload/Attachment
  
  // 7. Content Management Functions
  // - savePage
  // - createPage
  // - deletePage
  // - revertToRevision
  // - processMarkdown
  
  // 8. API Calls
  // - getPage
  // - updatePage
  // - searchPages
  // - getPageHistory
  // - getCategories
  // - uploadAttachment
  // - getRecentChanges
  // - authenticate
  
  // 9. Utility Functions
  // - formatDate
  // - generateTableOfContents
  // - highlightSearchTerms
  // - validatePageTitle
  // - processInternalLinks
  
  // 10. Render Methods
  // - renderPageView()
  // - renderPageEditor()
  // - renderSearchResults()
  // - renderVersionHistory()
  // - renderCategoriesView()
  // - renderNavigation()
  // - renderAuthView()
  
  return (
    <main className="wiki-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Wiki Homepage and Navigation**
   - Main page with featured articles and recent changes
   - Sidebar navigation with categories and popular pages
   - Search bar with autocomplete suggestions
   - User dashboard with contributions and watchlist
   - Quick access to frequently edited pages
   - Random page discovery button
   - Site statistics and activity overview

2. **Page Viewing Interface**
   - Clean article layout with typography optimization
   - Table of contents with anchor navigation
   - Article metadata (author, last edited, categories)
   - Page actions (edit, history, discuss, watch)
   - Related pages and suggested reading
   - Print-friendly formatting options
   - Social sharing and citation tools

3. **Page Editor with Live Preview**
   - Split-pane markdown editor with syntax highlighting
   - Live preview with real-time rendering
   - Toolbar with formatting shortcuts and helpers
   - Insert link dialog with page search
   - Image and file upload interface
   - Template insertion and snippet library
   - Auto-save with draft management
   - Edit conflict detection and resolution

4. **Version History and Comparison**
   - Timeline view of page revisions
   - Side-by-side diff visualization
   - Revision details with edit summaries
   - Revert functionality with confirmation
   - Contributor information and statistics
   - Blame view showing line-by-line authors
   - Export and download revision options

5. **Search and Discovery Interface**
   - Advanced search with multiple filters
   - Search results with snippet previews
   - Search highlighting and term relevance
   - Category browsing with page listings
   - Tag-based content discovery
   - Recent changes feed with filtering
   - Popular and trending pages dashboard

6. **Content Organization Tools**
   - Category management and hierarchy
   - Page tagging with autocomplete
   - Link management and broken link detection
   - Orphaned pages and wanted pages lists
   - Content statistics and analytics
   - Batch operations for page management
   - Export and backup functionality

## Markdown Editor Features

```javascript
// Advanced markdown editing:
const EditorFeatures = {
  // - Syntax highlighting for markdown
  // - Live preview with scroll synchronization
  // - Auto-completion for page links and templates
  // - Toolbar with formatting shortcuts
  // - Table editor with visual interface
  // - Math formula support with LaTeX
  // - Code block syntax highlighting
  // - Image drag-and-drop with automatic upload
};
```

## Page Navigation and Linking

- **Intelligent page linking** with autocomplete
- **Breadcrumb navigation** for hierarchical content
- **Table of contents** generation from headers
- **Cross-reference tracking** and backlink display
- **Related pages** suggestions based on content
- **Category-based navigation** with filtering
- **Search-driven discovery** with relevance ranking
- **Recently viewed** pages for quick access

## Version Control Interface

- **Visual diff comparison** with syntax highlighting
- **Timeline view** of all page revisions
- **Conflict resolution** tools for collaborative editing
- **Revert functionality** with impact assessment
- **Edit summaries** and change documentation
- **Contributor tracking** and attribution
- **Protected content** indicators and warnings
- **Draft management** with auto-save recovery

## UI/UX Requirements

- Clean, knowledge-focused interface design
- Typography optimized for reading and comprehension
- Mobile-first responsive layout
- Fast page loading with progressive enhancement
- Keyboard shortcuts for power users
- Accessibility compliance (screen readers, keyboard navigation)
- Print-friendly page layouts
- Loading states for content operations
- Error handling with helpful suggestions
- Dark/Light reading modes

## Collaborative Features Interface

```javascript
// Collaborative editing functionality:
const CollaborativeFeatures = {
  // - Real-time edit notifications
  // - User presence indicators during editing
  // - Edit conflict detection and warnings
  // - Discussion pages and talk functionality
  // - Watchlist and page monitoring
  // - User contribution tracking
  // - Vandalism detection and reporting
  // - Community moderation tools
};
```

## Search and Discovery Interface

- **Full-text search** with instant results
- **Advanced search** with boolean operators
- **Category browsing** with hierarchical navigation
- **Tag-based filtering** and content clustering
- **Search suggestions** and query completion
- **Search result highlighting** with context
- **Saved searches** and custom filters
- **Popular content** and trending topics

## Content Management Interface

- **Rich text formatting** with markdown support
- **Media management** with drag-and-drop upload
- **Template system** for reusable content blocks
- **Link validation** and broken link detection
- **Content templates** for different page types
- **Bulk editing** tools for administrative tasks
- **Content export** in multiple formats
- **Backup and versioning** with cloud sync

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Page API functions:
// - getPages(filters, pagination)
// - getPage(slug)
// - createPage(pageData)
// - updatePage(slug, pageData)
// - deletePage(slug)

// Version API functions:
// - getPageHistory(slug)
// - getRevision(slug, revisionId)
// - revertPage(slug, revisionId)
// - comparRevisions(slug, rev1, rev2)

// Search API functions:
// - searchPages(query, filters)
// - getCategories()
// - getRecentChanges()
// - getPopularPages()

// Content API functions:
// - uploadAttachment(pageSlug, file)
// - getPageLinks(slug)
// - getBacklinks(slug)
// - validateLinks(pageContent)
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
    <title>Wiki Platform</title>
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
   - Include React, Vite, markdown processing libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Offline editing with sync capabilities
   - Responsive design with mobile optimization
   - Proper state management for wiki content
   - Performance optimization (lazy loading, caching)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (keyboard shortcuts, auto-save)
   - SEO optimization for wiki content
   - Progressive Web App features

**Very important:** Your frontend should be feature rich, production ready, and provide excellent wiki experience with intuitive content editing, comprehensive search capabilities, collaborative features, and responsive design optimized for knowledge sharing and documentation.