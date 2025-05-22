# Frontend Generation Prompt - React File Storage Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (files, upload, shares, settings, trash).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**File Storage System Frontend**  
A modern React frontend for cloud storage application, featuring intuitive file management, drag-and-drop uploads, folder navigation, sharing controls, and storage analytics with enterprise-grade user experience.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Drag-and-drop file upload with progress tracking
- Hierarchical folder navigation with breadcrumbs
- File sharing with permission controls
- Storage quota visualization and management
- Advanced file type filtering and search
- Multiple view modes (grid, list, details)
- Responsive design with mobile optimization
- Real-time storage usage updates

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (files, upload, shares, settings, trash, auth)
  // - currentFolder and folder hierarchy
  // - files and folders arrays
  // - selectedItems for bulk operations
  // - uploadQueue and progress
  // - user authentication state
  // - storage quota and usage
  // - viewMode (grid, list, details)
  // - searchQuery and filters
  // - loading states
  // - error states

  // 4. Refs
  // - fileInputRef for upload
  // - dragDropRef for drag operations
  // - folderNavigationRef
  // - contextMenuRef
  
  // 5. Lifecycle Functions
  // - Load files and folders on mount
  // - Check user authentication
  // - Setup keyboard shortcuts
  // - Initialize storage monitoring
  
  // 6. Event Handlers
  // - handleFileUpload/DragDrop
  // - handleFolderNavigation
  // - handleItemSelect/Deselect
  // - handleShare/Unshare
  // - handleMove/Copy/Delete
  // - handleSearch/Filter
  // - handleAuth (login/register/logout)
  // - handleContextMenu
  
  // 7. File Management Functions
  // - uploadFiles
  // - createFolder
  // - moveItems
  // - copyItems
  // - deleteItems
  // - shareFile
  
  // 8. API Calls
  // - getFiles
  // - uploadFile
  // - createFolder
  // - deleteItem
  // - shareFile
  // - searchFiles
  // - getQuotaInfo
  // - authenticate
  
  // 9. Utility Functions
  // - formatFileSize
  // - formatDate
  // - getFileIcon
  // - calculateFolderSize
  // - validateFileName
  
  // 10. Render Methods
  // - renderFileExplorer()
  // - renderUploadArea()
  // - renderShareManager()
  // - renderStorageStats()
  // - renderAuthView()
  // - renderFileItem()
  // - renderFolderBreadcrumbs()
  
  return (
    <main className="storage-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **File Explorer View**
   - Hierarchical folder navigation with breadcrumbs
   - File and folder grid/list with thumbnails
   - Multi-select with checkboxes
   - Context menu with file operations
   - Drag-and-drop file organization
   - Search bar with real-time filtering
   - Sort options (name, size, date, type)
   - View mode toggles (grid, list, details)

2. **File Upload Interface**
   - Large drag-and-drop upload area
   - File browser button for traditional upload
   - Multiple file selection support
   - Upload progress bars with cancel option
   - Folder upload support (if browser allows)
   - Upload queue management
   - Error handling for failed uploads
   - Auto-folder creation during upload

3. **Folder Navigation System**
   - Expandable folder tree in sidebar
   - Breadcrumb navigation at top
   - Quick access to recent folders
   - Folder creation and management
   - Folder sharing and permissions
   - Nested folder support
   - Folder size and file count display

4. **File Sharing Management**
   - Share link generation with settings
   - Permission controls (view, download)
   - Expiry date selection
   - Password protection options
   - Active shares dashboard
   - Share analytics and access logs
   - Bulk sharing operations
   - Share link revocation

5. **Storage Analytics Dashboard**
   - Visual storage quota with usage bars
   - File type breakdown with charts
   - Largest files and folders identification
   - Storage usage trends over time
   - Cleanup suggestions and recommendations
   - Upload/download activity graphs
   - Storage optimization tips

6. **Search and Filter Interface**
   - Advanced search with multiple criteria
   - File type filters with icons
   - Date range selection
   - Size-based filtering
   - Tag-based search and organization
   - Saved search queries
   - Search within specific folders
   - Recent searches history

## File Management Features

```javascript
// Advanced file operations:
const FileManagementFeatures = {
  // - Drag-and-drop between folders
  // - Bulk operations (move, copy, delete)
  // - Right-click context menus
  // - Keyboard shortcuts (Ctrl+C, Ctrl+V, Delete)
  // - File preview for common types
  // - Rename inline editing
  // - Duplicate detection and handling
  // - Trash/recycle bin with recovery
};
```

## Upload Interface Features

- **Drag-and-drop upload** with visual feedback
- **Progress tracking** for individual files and batches
- **Upload queue management** with pause/resume
- **Automatic retry** for failed uploads
- **Upload speed** and ETA display
- **Folder structure preservation** during upload
- **Duplicate file handling** with user choice
- **Background uploading** with notifications

## Folder Navigation Features

- **Hierarchical breadcrumbs** with click navigation
- **Sidebar folder tree** with expand/collapse
- **Quick access** to frequently used folders
- **Recent folders** history
- **Folder bookmarks** and favorites
- **Nested folder creation** with templates
- **Folder search** and filtering
- **Folder size calculation** and display

## UI/UX Requirements

- Clean, modern cloud storage interface design
- Mobile-first responsive layout
- Fast file operations with optimistic updates
- Smooth animations and transitions
- Visual feedback for all user interactions
- Loading states for file operations
- Error handling with helpful suggestions
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for mobile devices
- Dark/Light theme support

## Sharing and Collaboration Interface

```javascript
// Advanced sharing functionality:
const SharingFeatures = {
  // - One-click share link generation
  // - Granular permission controls
  // - Bulk sharing for multiple files
  // - Share analytics with view counts
  // - Password-protected shares
  // - Time-limited access links
  // - Share notification system
  // - Collaborative folder access
};
```

## Storage Management Interface

- **Real-time quota visualization** with progress bars
- **Storage breakdown** by file types and folders
- **Usage alerts** when approaching limits
- **Cleanup recommendations** for large/old files
- **Storage optimization** suggestions
- **Usage trends** and analytics
- **File compression** options
- **Archive management** for old files

## Search and Discovery Interface

- **Real-time search** with instant results
- **Advanced filters** with multiple criteria
- **Tag-based organization** and filtering
- **Smart search suggestions** based on history
- **Search within results** refinement
- **Saved search** queries and alerts
- **Global search** across all files
- **Search result highlighting** and preview

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// File API functions:
// - getFiles(folderId, sort, filter)
// - uploadFiles(files, folderId)
// - downloadFile(id)
// - deleteFile(id)
// - moveFile(id, targetFolderId)
// - copyFile(id, targetFolderId)

// Folder API functions:
// - getFolders()
// - createFolder(name, parentId)
// - updateFolder(id, data)
// - deleteFolder(id)

// Sharing API functions:
// - createShare(fileId, permissions)
// - getShares()
// - revokeShare(shareId)

// Storage API functions:
// - getQuotaInfo()
// - searchFiles(query, filters)
// - getActivityLog()
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
    <title>File Storage</title>
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
   - Include React, Vite, file handling libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Progressive file loading with lazy loading
   - Responsive design with mobile optimization
   - Proper state management for large file collections
   - Performance optimization (virtualization, caching)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Progressive Web App features
   - Offline file access capabilities

**Very important:** Your frontend should be feature rich, production ready, and provide excellent cloud storage experience with intuitive file management, seamless upload/download, comprehensive sharing controls, and responsive design that works across all devices.