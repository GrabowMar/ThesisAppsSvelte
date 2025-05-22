# Frontend Generation Prompt - React File Uploader Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (upload, files list, folders, preview).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**File Uploader System Frontend**  
A modern React frontend for file upload application, featuring drag-and-drop upload, file management, preview capabilities, and organization tools with intuitive, responsive design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Drag-and-drop file upload interface
- Multiple file selection and batch upload
- Real-time upload progress tracking
- File listing with multiple view modes
- File preview and download functionality
- Folder/category organization
- Search and filtering capabilities
- Responsive design with mobile support

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (upload, files, folders, preview)
  // - uploadedFiles array with metadata
  // - selectedFiles for upload
  // - uploadProgress tracking
  // - currentFolder and folder structure
  // - selectedFile for preview
  // - searchQuery and filters
  // - loading states
  // - error states
  // - drag-and-drop states

  // 4. Refs
  // - fileInputRef for programmatic file selection
  // - dragOverlayRef for drag feedback
  // - uploadProgressRef
  
  // 5. Lifecycle Functions
  // - Load files and folders on mount
  // - Setup drag-and-drop event listeners
  // - Initialize upload progress tracking
  
  // 6. Event Handlers
  // - handleFileSelect (click and drag-drop)
  // - handleUpload/BatchUpload
  // - handleFileDelete/Download
  // - handleFolderCreate/Navigate
  // - handleSearch/Filter
  // - handlePreview
  // - handleDragEvents
  
  // 7. Upload Management
  // - uploadFiles (with progress tracking)
  // - validateFiles (size, type)
  // - generatePreviews
  // - trackUploadProgress
  
  // 8. API Calls
  // - uploadFile
  // - getFiles
  // - downloadFile
  // - deleteFile
  // - createFolder
  // - searchFiles
  // - getStorageStats
  
  // 9. Utility Functions
  // - formatFileSize
  // - formatDate
  // - getFileIcon
  // - validateFileType
  // - generateThumbnail
  
  // 10. Render Methods
  // - renderUploadArea()
  // - renderFilesList()
  // - renderFoldersView()
  // - renderFilePreview()
  // - renderUploadProgress()
  // - renderNavigation()
  
  return (
    <main className="file-uploader-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Upload Interface View**
   - Large drag-and-drop zone with visual feedback
   - File selection button for traditional upload
   - Multiple file selection support
   - File validation with error display
   - Upload queue with progress bars
   - Batch upload controls (pause, resume, cancel)
   - File type and size limit indicators

2. **Files List View**
   - Grid and list view toggle options
   - File cards/rows with thumbnails and metadata
   - Sort options (name, size, date, type)
   - Bulk selection with checkboxes
   - Context menu for file operations
   - Search bar with real-time filtering
   - Pagination for large file collections

3. **File Preview View**
   - Large preview area for supported file types
   - Image viewer with zoom and navigation
   - Text file content display
   - Document preview (if supported)
   - File metadata panel (size, type, upload date)
   - Download and delete buttons
   - Share/copy link functionality

4. **Folder Management View**
   - Folder tree navigation
   - Create new folder interface
   - Drag-and-drop file organization
   - Breadcrumb navigation
   - Folder statistics (file count, total size)
   - Nested folder support

5. **Upload Progress Components**
   - Individual file progress indicators
   - Overall batch upload progress
   - Upload speed and ETA display
   - Success/error notifications
   - Retry failed upload option
   - Upload history and logs

6. **Navigation and Search**
   - Top toolbar with navigation options
   - Advanced search with filters
   - Quick filter buttons (images, documents, recent)
   - Storage usage indicator
   - View mode toggles

## Drag-and-Drop Features

```javascript
// Advanced drag-and-drop functionality:
const DragDropFeatures = {
  // - Visual feedback during drag operations
  // - Multiple file drop support
  // - Folder drag-and-drop (if browser supports)
  // - File type validation on drop
  // - Drag-to-organize files into folders
  // - Preview generation during drag
  // - Cancel drag operations
  // - Accessibility support for drag-drop
};
```

## Upload Progress and Management

- **Real-time progress tracking** for individual files and batches
- **Upload speed calculation** and time remaining estimates
- **Pause/Resume functionality** for large file uploads
- **Retry mechanism** for failed uploads
- **Upload queue management** with reordering capabilities
- **Background uploads** with notification system
- **Upload history** and status tracking

## File Preview Capabilities

- **Image preview** with zoom, rotate, and basic editing
- **Text file display** with syntax highlighting for code
- **PDF preview** using embedded viewer
- **Video/Audio players** for media files
- **Archive file listing** for ZIP files
- **Metadata display** for all file types
- **Fullscreen preview** mode

## UI/UX Requirements

- Clean, modern file management interface
- Responsive design (mobile-first approach)
- Fast file operations with visual feedback
- Intuitive drag-and-drop interactions
- Loading states for all operations
- Error handling with user-friendly messages
- Keyboard shortcuts for power users
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for mobile devices
- Smooth animations and transitions

## File Management Features

```javascript
// Comprehensive file operations:
const FileOperations = {
  // - Bulk select and operations
  // - Copy/Move files between folders
  // - Rename files and folders
  // - Duplicate detection and handling
  // - File sharing and link generation
  // - Download as ZIP for multiple files
  // - File history and versioning
  // - Favorites and bookmarks
};
```

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Upload API functions:
// - uploadFile(file, onProgress)
// - uploadMultipleFiles(files, onProgress)
// - resumeUpload(uploadId)
// - cancelUpload(uploadId)

// File Management API functions:
// - getFiles(folder, page, sort, filter)
// - getFileMetadata(id)
// - downloadFile(id)
// - deleteFile(id)
// - moveFile(id, folderId)

// Folder API functions:
// - getFolders()
// - createFolder(name, parentId)
// - deleteFolder(id)

// Search API functions:
// - searchFiles(query, filters)
// - getStorageStats()
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
    <title>File Uploader</title>
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
   - Upload progress tracking and management
   - Responsive design with mobile optimization
   - Proper state management for file operations
   - Performance optimization (lazy loading, virtualization)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Offline functionality detection
   - Memory management for large file operations

**Very important:** Your frontend should be feature rich, production ready, and provide excellent file management experience with intuitive drag-and-drop interface, robust upload handling, comprehensive file organization, and responsive design that works across all devices.