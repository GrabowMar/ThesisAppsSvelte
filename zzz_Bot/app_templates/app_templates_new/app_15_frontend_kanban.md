# Frontend Generation Prompt - React Kanban Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (boards, kanban, task details, team, settings).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Kanban System Frontend**  
A modern React frontend for Kanban task management application, featuring interactive drag-and-drop boards, task management, team collaboration, and real-time updates with professional, responsive design.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Interactive Kanban board with drag-and-drop functionality
- Task creation, editing, and management interface
- Column organization with customizable layouts
- Advanced filtering and search capabilities
- Team collaboration features
- Real-time updates and notifications
- Mobile-responsive design
- Touch-friendly interactions for mobile devices

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (boards, kanban, task-detail, team, settings, auth)
  // - boards array
  // - currentBoard with columns and tasks
  // - selectedTask for editing
  // - dragState for drag-and-drop
  // - user authentication state
  // - team members array
  // - filters and search state
  // - notifications array
  // - loading states
  // - error states

  // 4. Refs
  // - boardRef for scroll management
  // - dragPreviewRef
  // - taskModalRef
  // - dropZoneRefs for columns
  
  // 5. Lifecycle Functions
  // - Load boards and user data on mount
  // - Check user authentication
  // - Setup real-time updates
  // - Initialize drag-and-drop handlers
  
  // 6. Event Handlers
  // - handleTaskDragStart/Drop/End
  // - handleTaskCreate/Edit/Delete
  // - handleColumnCreate/Edit/Delete
  // - handleBoardCreate/Edit/Delete
  // - handleFilter/Search
  // - handleAuth (login/register/logout)
  // - handleRealTimeUpdates
  
  // 7. Drag-and-Drop Functions
  // - onDragStart
  // - onDragOver
  // - onDrop
  // - updateTaskPosition
  // - calculateDropPosition
  
  // 8. API Calls
  // - getBoards
  // - getBoard
  // - createTask
  // - updateTask
  // - moveTask
  // - createColumn
  // - updateColumn
  // - deleteTask
  // - searchTasks
  // - authenticate
  
  // 9. Utility Functions
  // - formatDate
  // - calculateTaskStats
  // - validateTaskData
  // - generateTaskId
  // - filterTasks
  
  // 10. Render Methods
  // - renderBoardsList()
  // - renderKanbanBoard()
  // - renderColumn()
  // - renderTask()
  // - renderTaskModal()
  // - renderTeamView()
  // - renderAuthView()
  
  return (
    <main className="kanban-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 11. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Boards List View**
   - Grid of board cards with thumbnails
   - Create new board button with templates
   - Board search and filtering
   - Recent boards and favorites
   - Board sharing status indicators
   - Quick board statistics
   - Board settings and permissions

2. **Kanban Board View**
   - Horizontal scrolling board layout
   - Draggable columns with custom names
   - Drag-and-drop task cards between columns
   - Column headers with task counts and WIP limits
   - Add new task and column buttons
   - Board header with name, description, and controls
   - Real-time collaboration indicators

3. **Task Management Interface**
   - Task creation modal with form fields
   - Task detail view with rich editing
   - Task assignment with team member selection
   - Due date picker with calendar integration
   - Priority levels with visual indicators
   - Labels and tags management
   - Task comments and activity timeline
   - File attachments support

4. **Column Organization System**
   - Column creation and editing modals
   - Drag-and-drop column reordering
   - WIP limit settings with visual warnings
   - Column color customization
   - Column-specific filtering options
   - Column analytics and metrics
   - Archive and restore column functionality

5. **Search and Filter Interface**
   - Global search across all boards and tasks
   - Advanced filters (assignee, labels, due date, priority)
   - Quick filter buttons for common scenarios
   - Saved filter sets and views
   - Search suggestions and autocomplete
   - Filter combination with visual chips
   - Clear all filters option

6. **Team Collaboration View**
   - Team member list with avatars and roles
   - User activity feed and status
   - Team invitation and management
   - Permission settings and role assignment
   - Team statistics and productivity metrics
   - Member profile pages

## Drag-and-Drop Features

```javascript
// Advanced drag-and-drop functionality:
const DragDropFeatures = {
  // - Smooth drag animations with visual feedback
  // - Auto-scroll when dragging near edges
  // - Drop zone highlighting and validation
  // - Multi-select drag for bulk operations
  // - Touch gesture support for mobile
  // - Keyboard accessibility for drag operations
  // - Undo/redo for drag operations
  // - Conflict resolution for simultaneous moves
};
```

## Task Management Interface

- **Rich task creation** with templates and quick add
- **Inline editing** for task titles and descriptions
- **Bulk operations** for multiple task management
- **Task copying** and templating
- **Subtask management** with progress tracking
- **Task linking** and dependencies
- **Time tracking** with start/stop timers
- **Task archiving** and restoration

## Column Customization Features

- **Dynamic column addition** and removal
- **Column templates** for different workflows
- **WIP limit enforcement** with visual warnings
- **Column-specific automation** rules
- **Color coding** and visual customization
- **Column sorting** and filtering options
- **Column analytics** with flow metrics
- **Swimlane views** for advanced organization

## UI/UX Requirements

- Clean, modern Kanban interface design
- Mobile-first responsive layout
- Smooth drag-and-drop interactions
- Real-time visual updates
- Visual feedback for all user actions
- Loading states for board operations
- Error handling with helpful messages
- Accessibility compliance (ARIA labels, keyboard navigation)
- Touch-friendly interface for mobile devices
- Dark/Light theme support

## Real-time Collaboration Features

```javascript
// Real-time collaboration functionality:
const CollaborationFeatures = {
  // - Live cursors showing team member activity
  // - Real-time task updates across all users
  // - Conflict resolution for simultaneous edits
  // - Live typing indicators in task descriptions
  // - Push notifications for important changes
  // - Activity feed with real-time updates
  // - Presence indicators for team members
  // - Collaborative editing with version control
};
```

## Mobile and Touch Optimization

- **Touch-friendly drag-and-drop** with haptic feedback
- **Swipe gestures** for quick task actions
- **Mobile-optimized layouts** with collapsible sections
- **Touch-friendly button sizes** and spacing
- **Pull-to-refresh** for board updates
- **Mobile context menus** with action sheets
- **Responsive column sizing** for different screens
- **Touch accessibility** features

## Board Analytics and Insights

- **Task flow visualization** with burndown charts
- **Cycle time analysis** and bottleneck identification
- **Team productivity metrics** and trends
- **Column efficiency** statistics
- **Sprint progress tracking** with velocity charts
- **Custom dashboard** creation
- **Export capabilities** for reporting
- **Historical trend** analysis

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// Authentication API functions:
// - login(credentials)
// - register(userData)
// - logout()
// - getCurrentUser()

// Board API functions:
// - getBoards()
// - getBoard(id)
// - createBoard(boardData)
// - updateBoard(id, boardData)
// - deleteBoard(id)

// Task API functions:
// - getTasks(boardId)
// - getTask(id)
// - createTask(taskData)
// - updateTask(id, taskData)
// - deleteTask(id)
// - moveTask(id, columnId, position)

// Column API functions:
// - getColumns(boardId)
// - createColumn(columnData)
// - updateColumn(id, columnData)
// - deleteColumn(id)
// - reorderColumns(boardId, columnOrder)

// Team API functions:
// - getTeamMembers()
// - inviteUser(email, boardId)
// - updateUserRole(userId, role)
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
    <title>Kanban Board</title>
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
   - Include React, Vite, drag-and-drop libraries, and any additional libraries needed

3. **Production Ready Features**
   - Comprehensive error handling and recovery
   - Real-time updates with optimistic UI
   - Responsive design with mobile optimization
   - Proper state management for complex board data
   - Performance optimization (virtualization for large boards)
   - Accessibility compliance
   - Clean code with comments
   - User experience enhancements (smooth animations, shortcuts)
   - Progressive Web App features
   - Offline functionality with sync

**Very important:** Your frontend should be feature rich, production ready, and provide excellent Kanban board experience with intuitive drag-and-drop interface, comprehensive task management, real-time collaboration features, and responsive design that works across all devices.