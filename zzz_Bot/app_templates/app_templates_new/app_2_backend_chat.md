# Backend Generation Prompt - Flask Chat Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and real-time capabilities.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/messages`, `/api/rooms`, `/api/users`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Chat System Backend**  
A real-time Flask backend for chat application, featuring message exchange, user management, and chat room capabilities with WebSocket support.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Real-time message exchange (WebSocket/Server-Sent Events)
- User identification and management
- Message history storage and retrieval
- Online status tracking
- Chat rooms management
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import sqlite3
from datetime import datetime
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# 3. Database Models/Setup
# 4. User Management Logic
# 5. Message Handling Logic
# 6. Room Management Logic
# 7. API Routes:
#    - POST /api/join (join chat)
#    - GET /api/messages/<room_id>
#    - GET /api/rooms
#    - GET /api/users/<room_id>
#    - POST /api/rooms (create room)
# 8. WebSocket Events:
#    - connect
#    - disconnect
#    - join_room
#    - leave_room
#    - send_message
#    - typing
# 9. Error Handlers

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

1. **POST /api/join**
   - Accept: username, room_id (optional)
   - Generate user session
   - Return user info and available rooms

2. **GET /api/messages/<room_id>**
   - Return message history for specific room
   - Include pagination support
   - Return user info with messages

3. **GET /api/rooms**
   - Return list of available chat rooms
   - Include room metadata (user count, etc.)

4. **GET /api/users/<room_id>**
   - Return list of users in specific room
   - Include online status

5. **POST /api/rooms**
   - Create new chat room
   - Accept: room_name, description
   - Return room info

## Required WebSocket Events

1. **connect**
   - Handle user connection
   - Track online status

2. **disconnect**
   - Handle user disconnection
   - Update online status
   - Notify room members

3. **join_room**
   - Add user to specific room
   - Broadcast join notification
   - Send room info

4. **leave_room**
   - Remove user from room
   - Broadcast leave notification

5. **send_message**
   - Accept: room_id, message, user_id
   - Store message in database
   - Broadcast to room members

6. **typing**
   - Handle typing indicators
   - Broadcast typing status to room

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT)
- joined_at (TIMESTAMP)
- last_seen (TIMESTAMP)

Rooms table:
- id (TEXT PRIMARY KEY)
- name (TEXT)
- description (TEXT)
- created_at (TIMESTAMP)

Messages table:
- id (INTEGER PRIMARY KEY)
- room_id (TEXT)
- user_id (TEXT)
- username (TEXT)
- content (TEXT)
- timestamp (TIMESTAMP)

User_Rooms table:
- user_id (TEXT)
- room_id (TEXT)
- joined_at (TIMESTAMP)
```

## Real-time Features

- WebSocket connections for instant messaging
- Typing indicators
- Online/offline status updates
- Real-time user join/leave notifications
- Message delivery confirmations
- Room member updates

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in socketio.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-SocketIO, Flask-CORS, etc.

3. **Production Ready Features**
   - Comprehensive error handling
   - WebSocket connection management
   - Message persistence
   - Room management
   - User session handling
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all real-time messaging scenarios including connection drops, room management, and message persistence.