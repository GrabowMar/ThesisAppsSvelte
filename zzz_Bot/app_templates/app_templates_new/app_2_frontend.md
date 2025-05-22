# Frontend Generation Prompt - React Chat Application

## Important Implementation Notes

1. Generate a React frontend with properly implemented key features mentioned below.
2. Keep all frontend logic within **App.jsx** and styles in **App.css** files.
3. Write feature complete production ready app, with comments, loading states, error handling, etc.
4. **Note:** Implement client-side routing within **App.jsx** using conditional rendering for different views (join, chat rooms, main chat).
5. **Mounting Logic:** The App.jsx file must include mounting logic with ReactDOM from react-dom/client to attach the App component to DOM element with id "root".
6. Use port **XXXX** for the frontend development server.

## Project Description

**Chat System Frontend**  
A modern React frontend for real-time chat application, featuring instant messaging, chat rooms, and user interaction with clean, responsive UI.

**Required Features:**
- **Multipage Routing:** Client-side routing within App.jsx for different views
- Simple and modern UI design
- Real-time message exchange
- User identification interface
- Message history display
- Online status indicators
- Chat rooms interface
- Typing indicators
- Responsive design

## Frontend Structure (App.jsx)

```jsx
// 1. Imports
import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import io from 'socket.io-client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  // - currentView (join, chat)
  // - user info (username, userId)
  // - messages array
  // - rooms array
  // - currentRoom
  // - onlineUsers
  // - typingUsers
  // - socket connection
  // - loading states

  // 4. Refs
  // - messagesEndRef for auto-scroll
  // - messageInputRef for focus management
  
  // 5. Lifecycle Functions
  // - Initialize socket connection
  // - Setup event listeners
  // - Cleanup on unmount
  
  // 6. Event Handlers
  // - handleJoinChat
  // - handleSendMessage
  // - handleRoomChange
  // - handleTyping
  // - handleDisconnect
  
  // 7. Socket Event Handlers
  // - onConnect
  // - onDisconnect
  // - onMessage
  // - onUserJoined
  // - onUserLeft
  // - onTyping
  // - onRoomUpdate
  
  // 8. API Calls
  // - joinChat
  // - getMessages
  // - getRooms
  // - createRoom
  
  // 9. Render Methods
  // - renderJoinView()
  // - renderChatView()
  // - renderMessageList()
  // - renderUserList()
  // - renderRoomList()
  
  return (
    <main className="chat-app">
      {/* Conditional rendering based on currentView */}
    </main>
  );
}

// 10. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

## Required Views/Components

1. **Join View**
   - Username input field
   - Room selection dropdown
   - Join button
   - Create new room option
   - Error display
   - Loading state

2. **Chat View**
   - Header with room name and online count
   - Message list with scroll
   - Message input with send button
   - User list sidebar
   - Room switching interface
   - Typing indicators
   - Disconnect/leave button

3. **Message Components**
   - Individual message display
   - Timestamp formatting
   - Username styling
   - System messages (join/leave)
   - Message status indicators

4. **User Interface Elements**
   - Online user list
   - User status indicators
   - Typing notifications
   - Room member count
   - Connection status

## Real-time Features

```javascript
// Socket.IO integration
const socket = io('http://localhost:YYYY');

// Event listeners:
// - message
// - user_joined
// - user_left
// - typing
// - stop_typing
// - room_update
// - connect
// - disconnect

// Event emitters:
// - join_room
// - leave_room
// - send_message
// - typing
// - stop_typing
```

## UI/UX Requirements

- Clean, modern chat interface
- Real-time message updates
- Smooth scrolling to new messages
- Responsive layout (mobile-friendly)
- Typing indicators
- Online status visualization
- Message timestamps
- Auto-focus on message input
- Keyboard shortcuts (Enter to send)
- Connection status indicators

## API Integration

```javascript
// Base API configuration
const API_BASE = '/api';

// API functions:
// - joinChat(username, roomId)
// - getMessages(roomId, page)
// - getRooms()
// - createRoom(roomData)
// - getUsers(roomId)
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
      },
      '/socket.io': {
        target: 'http://localhost:YYYY',
        changeOrigin: true,
        ws: true,
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
    <title>Chat Application</title>
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
   - Proxy API calls and WebSocket to backend on port `YYYY`

2. **Dependencies**
   - Generate complete package.json with all necessary npm dependencies
   - Include React, Vite, Socket.IO client, and any additional libraries needed

3. **Production Ready Features**
   - Real-time connection management
   - Error boundaries and fallbacks
   - Loading states for all operations
   - Responsive design
   - Proper state management
   - Message persistence during view changes
   - Auto-reconnection handling
   - Clean code with comments

**Very important:** Your frontend should be feature rich, production ready, and provide excellent real-time chat experience with proper connection handling, message display, and user interaction features.