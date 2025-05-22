# Frontend Generation Prompt - React Gallery Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (gallery, albums, upload, image viewer, settings).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Gallery System Frontend**  
A modern React frontend for gallery application, featuring intuitive image management, responsive photo viewing, album organization, and upload workflows with beautiful, touch-friendly design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Drag-and-drop image upload with progress tracking
- Multiple gallery view modes (grid, list, masonry)
- Full-screen image viewer with navigation
- Album creation and management interface
- Image metadata display and editing
- Search and filtering capabilities
- Responsive design with mobile optimization
- Touch gestures for image navigation

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (gallery, albums, upload, viewer, settings, auth)
  // - images array with pagination
  // - albums array
  // - currentImage for viewer
  // - selectedImages for bulk operations
  // - uploadQueue and progress
  // - user authentication state
  // - viewMode (grid, list, masonry)
  // - filters and search state
  // - loading states
  // - error states

  // 4. Refs
  // - fileInputRef for upload
  // - galleryGridRef for virtualization
  // - imageViewerRef
  // - dragDropRef
  
  // 5. Lifecycle Functions
  // - Load images and albums on mount
  // - Check user authentication
  // - Setup keyboard shortcuts
  // - Initialize touch gestures
  
  // 6. Event Handlers
  // - handleImageUpload/DragDrop
  // - handleImageSelect/Deselect
  // - handleViewModeChange
  // - handleAlbumCreate/Edit/Delete
  // - handleImageView/Navigate
  // - handleSearch/Filter
  // - handleAuth (login/register/logout)
  // - handleKeyboardNavigation
  
  // 7. Gallery Functions
  // - uploadImages
  // - createAlbum
  // - moveImagesToAlbum
  // - deleteImages
  // - updateImageMetadata
  
  // 8. API Calls
  // - getImages
  // - getImage
  // - uploadImage
  // - createAlbum
  // - updateAlbum
  // - deleteImage
  // - searchImages
  // - getTags
  // - authenticate
  
  // 9. Utility Functions
  // - formatFileSize
  // - formatDate
  // - generateThumbnail
  // - validateImageFile
  // - calculateImageDimensions
  
  // 10. Render Methods
  // - renderGalleryGrid()
  // - renderImageViewer()
  // - renderUploadArea()
  // - renderAlbumsView()
  // - renderAuthView()
  // - renderImageCard()
  // - renderAlbumCard()
  
  return (
    <main className="gallery-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Gallery Grid View**
   - Responsive image grid with multiple layout options
   - Infinite scroll or pagination
   - Image thumbnails with lazy loading
   - Hover effects with quick actions
   - Multi-select with checkboxes
   - Drag-and-drop reordering
   - Search bar and filter controls
   - View mode toggles (grid, list, masonry)

2. **Image Upload Interface**
   - Large drag-and-drop upload area
   - File browser button for traditional upload
   - Multiple file selection support
   - Upload progress bars for each image
   - Preview thumbnails during upload
   - Batch upload controls
   - Error handling for failed uploads
   - Album assignment during upload

3. **Full-Screen Image Viewer**
   - Large image display with zoom functionality
   - Navigation arrows and keyboard controls
   - Image information sidebar (metadata, EXIF)
   - Social sharing buttons
   - Download and delete options
   - Slideshow mode with auto-advance
   - Touch gestures for mobile navigation
   - Background thumbnails strip

4. **Albums Management View**
   - Album grid with cover images
   - Create/edit/delete album functionality
   - Album details with image counts
   - Drag-and-drop image organization
   - Album privacy settings
   - Cover image selection
   - Album sharing options
   - Search within albums

5. **Image Details and Metadata**
   - Editable title and description
   - EXIF data display (camera, settings, location)
   - Tag management with autocomplete
   - File information (size, dimensions, format)
   - Upload date and view statistics
   - Location information if available
   - Related images suggestions

6. **Search and Filter Interface**
   - Advanced search with multiple criteria
   - Tag-based filtering with suggestions
   - Date range selection
   - File type and size filters
   - Album-specific search
   - Saved search queries
   - Search result highlighting

## Image Viewing Features

```javascript
// Advanced image viewer functionality:
const ImageViewerFeatures = {
  // - Smooth zoom in/out with mouse wheel and pinch
  // - Pan and drag for large images
  // - Fullscreen mode with ESC key exit
  // - Keyboard navigation (arrow keys, space)
  // - Touch gestures (swipe, pinch, double-tap)
  // - Image rotation and basic editing
  // - Slideshow with customizable timing
  // - Thumbnail navigation strip
};
```

## Upload and Processing Interface

- **Drag-and-drop upload** with visual feedback
- **Progress tracking** for individual files and batches
- **Upload queue management** with pause/resume
- **Automatic thumbnail generation** preview
- **Bulk metadata editing** during upload
- **Album assignment** before and after upload
- **Error handling** with retry options
- **File validation** with user feedback

## Gallery Organization Features

- **Multiple view modes** (grid, list, masonry, timeline)
- **Responsive grid** that adapts to screen size
- **Infinite scroll** or pagination options
- **Bulk selection** with keyboard shortcuts
- **Drag-and-drop** album management
- **Quick actions** on hover (view, edit, delete)
- **Sort options** (date, name, size, views)
- **Filter combinations** (tags, albums, dates)

## UI/UX Requirements

- Clean, modern gallery interface design
- Mobile-first responsive layout
- Fast image loading with progressive enhancement
- Smooth animations and transitions
- Visual feedback for all user interactions
- Loading states for image processing
- Error handling with user-friendly messages
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for mobile devices
- Dark/Light theme support

## Mobile and Touch Features

```javascript
// Mobile-optimized gallery:
const MobileFeatures = {
  // - Touch-friendly image grid with proper spacing
  // - Swipe gestures for image navigation
  // - Pinch-to-zoom in image viewer
  // - Pull-to-refresh for gallery updates
  // - Mobile-optimized upload interface
  // - Touch-friendly album management
  // - Responsive image sizing
  // - Mobile-specific context menus
};
```

## Album Management Interface

- **Visual album creation** with cover selection
- **Drag-and-drop** image organization
- **Album privacy controls** (public, private, shared)
- **Nested album** support with breadcrumbs
- **Album sharing** with link generation
- **Collaborative albums** with permissions
- **Album templates** for common use cases
- **Bulk album operations**

## Search and Discovery Interface

- **Real-time search** with instant results
- **Tag cloud** visualization for discovery
- **Advanced filters** with multi-criteria selection
- **Search suggestions** and autocomplete
- **Visual search** by similar images
- **Recent searches** and bookmarks
- **Search result organization** by relevance
- **Export search** results functionality

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Image API functions:
// - getImages(page, filters, sort)
// - getImage(id)
// - uploadImages(files, albumId)
// - updateImage(id, metadata)
// - deleteImage(id)
// - bulkDeleteImages(imageIds)

// Album API functions:
// - getAlbums()
// - createAlbum(albumData)
// - updateAlbum(id, albumData)
// - deleteAlbum(id)
// - addImagesToAlbum(albumId, imageIds)

// Search API functions:
// - searchImages(query, filters)
// - getTags()
// - getImageMetadata(id)
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
    <title>Gallery Application</title>
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
   - Include React, Vite, image processing libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Progressive image loading with lazy loading
   - Responsive design with mobile optimization
   - Proper state management for large galleries
   - Performance optimization (virtualization, caching)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, gestures)
   - Progressive Web App features
   - Offline viewing capabilities

**Very important:** Your frontend should be feature rich, production ready, and provide excellent gallery experience with intuitive image management, beautiful viewing interface, comprehensive organization tools, and responsive design that works across all devices.