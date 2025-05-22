# Backend Generation Prompt - Flask Kanban Application

## Important Implementation Notes

1. Generate a Flask backend with properly implemented key features mentioned below.
2. Keep all backend logic within **app.py** file.
3. Write feature complete production ready app, with comments, error handling, and proper validation.
4. **Note:** Implement multipage routing with multiple routes (e.g., `/api/boards`, `/api/tasks`, `/api/columns`, etc.) in **app.py**.
5. Use port **YYYY** for the backend server.

## Project Description

**Kanban System Backend**  
A comprehensive Flask backend for Kanban task management application, featuring board management, task tracking, column organization, team collaboration, and real-time updates with drag-and-drop support.

**Required Features:**
- **Multipage Routing:** Multiple API endpoints for different functionalities
- Complete board management system
- Task creation, editing, and lifecycle management
- Flexible column organization and customization
- Drag-and-drop task movement with position tracking
- Advanced filtering and search capabilities
- User authentication and team collaboration
- Activity logging and task history
- Real-time updates and notifications
- Sprint and milestone management
- CORS support for frontend communication
- Database integration (SQLite or in-memory for simplicity)

## Backend Structure (app.py)

```python
# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime, timedelta
import uuid
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'your-secret-key-here'

# 3. Database Models/Setup
# 4. Board Management Logic
# 5. Task Position Tracking
# 6. Activity Logging
# 7. API Routes:
#    - GET /api/boards (list boards)
#    - GET /api/boards/<id> (get board details)
#    - POST /api/boards (create board)
#    - PUT /api/boards/<id> (update board)
#    - DELETE /api/boards/<id> (delete board)
#    - GET /api/boards/<id>/columns (get board columns)
#    - POST /api/boards/<id>/columns (create column)
#    - PUT /api/columns/<id> (update column)
#    - DELETE /api/columns/<id> (delete column)
#    - POST /api/columns/<id>/move (reorder columns)
#    - GET /api/boards/<id>/tasks (get board tasks)
#    - GET /api/tasks/<id> (get task details)
#    - POST /api/tasks (create task)
#    - PUT /api/tasks/<id> (update task)
#    - DELETE /api/tasks/<id> (delete task)
#    - POST /api/tasks/<id>/move (move task between columns)
#    - GET /api/tasks/<id>/activity (get task activity)
#    - GET /api/search (search tasks and boards)
#    - GET /api/users (get team members)
#    - POST /api/users/invite (invite team member)
#    - POST /api/auth/register (user registration)
#    - POST /api/auth/login (user login)
#    - POST /api/auth/logout (user logout)
#    - GET /api/auth/user (get current user)
# 8. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'YYYY')))
```

## Required API Endpoints

### Authentication Routes

1. **POST /api/auth/register**
   - Accept: username, email, password, full_name
   - Validate input and create user account
   - Hash password securely
   - Return user info and session

2. **POST /api/auth/login**
   - Accept: username/email, password
   - Validate credentials
   - Create user session
   - Return user info

3. **POST /api/auth/logout**
   - Clear user session
   - Return success response

4. **GET /api/auth/user**
   - Return current authenticated user info
   - Include user preferences and settings

### Board Management Routes

5. **GET /api/boards**
   - Return list of boards user has access to
   - Include board metadata and member counts
   - Support filtering by ownership and participation

6. **GET /api/boards/<id>**
   - Return specific board with full details
   - Include columns, tasks, and team members
   - Check user permissions

7. **POST /api/boards**
   - Create new board
   - Accept: name, description, template, privacy_setting
   - Initialize default columns (To Do, In Progress, Done)
   - Return created board

8. **PUT /api/boards/<id>**
   - Update board details
   - Accept: name, description, settings
   - Require appropriate permissions
   - Return updated board

9. **DELETE /api/boards/<id>**
   - Delete board and all associated data
   - Require owner permissions
   - Clean up tasks, columns, and activities
   - Return confirmation

### Column Management Routes

10. **GET /api/boards/<id>/columns**
    - Return columns for specific board
    - Include column order and task counts
    - Support customization settings

11. **POST /api/boards/<id>/columns**
    - Create new column in board
    - Accept: name, position, wip_limit, color
    - Insert at specified position
    - Return created column

12. **PUT /api/columns/<id>**
    - Update column details
    - Accept: name, wip_limit, color, position
    - Validate WIP limits
    - Return updated column

13. **DELETE /api/columns/<id>**
    - Delete column
    - Handle tasks in column (move or delete)
    - Update column positions
    - Return confirmation

14. **POST /api/columns/<id>/move**
    - Reorder columns within board
    - Accept: new_position
    - Update all affected column positions
    - Return updated column order

### Task Management Routes

15. **GET /api/boards/<id>/tasks**
    - Return tasks for specific board
    - Include task details and assignments
    - Support filtering and sorting

16. **GET /api/tasks/<id>**
    - Return specific task with full details
    - Include comments, attachments, and activity
    - Check user permissions

17. **POST /api/tasks**
    - Create new task
    - Accept: title, description, column_id, assignee_id, due_date, priority
    - Set initial position in column
    - Return created task

18. **PUT /api/tasks/<id>**
    - Update task details
    - Accept: title, description, assignee_id, due_date, priority, labels
    - Log activity for changes
    - Return updated task

19. **DELETE /api/tasks/<id>**
    - Delete task
    - Remove from column and update positions
    - Log deletion activity
    - Return confirmation

20. **POST /api/tasks/<id>/move**
    - Move task between columns or positions
    - Accept: target_column_id, position
    - Update task positions in affected columns
    - Log movement activity

21. **GET /api/tasks/<id>/activity**
    - Return activity log for specific task
    - Include all changes, comments, and movements
    - Support pagination

### Search and Team Routes

22. **GET /api/search**
    - Search across tasks and boards
    - Accept: query, filters (board, assignee, labels, due_date)
    - Support advanced search operators
    - Return ranked results

23. **GET /api/users**
    - Return team members for user's boards
    - Include user profiles and activity status
    - Support role-based filtering

24. **POST /api/users/invite**
    - Invite user to board or team
    - Accept: email, board_id, role
    - Send invitation notification
    - Return invitation status

## Database Schema

```sql
Users table:
- id (TEXT PRIMARY KEY)
- username (TEXT UNIQUE NOT NULL)
- email (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL)
- full_name (TEXT)
- avatar_url (TEXT)
- created_at (TIMESTAMP)
- is_active (BOOLEAN DEFAULT TRUE)

Boards table:
- id (TEXT PRIMARY KEY)
- name (TEXT NOT NULL)
- description (TEXT)
- owner_id (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- is_private (BOOLEAN DEFAULT FALSE)
- background_color (TEXT)
- column_order (TEXT) -- JSON array of column IDs

Columns table:
- id (TEXT PRIMARY KEY)
- board_id (TEXT)
- name (TEXT NOT NULL)
- position (INTEGER)
- wip_limit (INTEGER)
- color (TEXT)
- created_at (TIMESTAMP)
- task_count (INTEGER DEFAULT 0)

Tasks table:
- id (TEXT PRIMARY KEY)
- board_id (TEXT)
- column_id (TEXT)
- title (TEXT NOT NULL)
- description (TEXT)
- assignee_id (TEXT)
- creator_id (TEXT)
- position (INTEGER)
- priority (TEXT) -- 'low', 'medium', 'high', 'urgent'
- due_date (TIMESTAMP)
- labels (TEXT) -- JSON array
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- completed_at (TIMESTAMP)

Board_Members table:
- board_id (TEXT)
- user_id (TEXT)
- role (TEXT) -- 'owner', 'admin', 'member', 'viewer'
- joined_at (TIMESTAMP)

Task_Activities table:
- id (TEXT PRIMARY KEY)
- task_id (TEXT)
- user_id (TEXT)
- action (TEXT) -- 'created', 'moved', 'updated', 'assigned', 'commented'
- details (TEXT) -- JSON with change details
- from_column_id (TEXT)
- to_column_id (TEXT)
- created_at (TIMESTAMP)

Task_Comments table:
- id (TEXT PRIMARY KEY)
- task_id (TEXT)
- user_id (TEXT)
- content (TEXT NOT NULL)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## Kanban Board Features

- **Flexible column management** with custom names and limits
- **Drag-and-drop task movement** with position tracking
- **Work-in-progress (WIP) limits** for columns
- **Task prioritization** with visual indicators
- **Label and tagging** system for organization
- **Due date tracking** with overdue notifications
- **Team collaboration** with role-based permissions
- **Activity logging** for audit trails

## Task Management Features

- **Rich task details** with descriptions and metadata
- **Task assignment** with team member notifications
- **Subtask support** with progress tracking
- **File attachments** and comments
- **Task templates** for recurring work
- **Bulk operations** for multiple tasks
- **Task dependencies** and blocking relationships
- **Time tracking** and estimation

## Real-time and Collaboration Features

- **Real-time updates** for board changes
- **Conflict resolution** for simultaneous edits
- **Activity notifications** for team members
- **Collaborative editing** with live cursors
- **Board sharing** with permission controls
- **Team workspace** management
- **Integration webhooks** for external tools

## Performance and Analytics Features

- **Board analytics** with task flow metrics
- **Burndown charts** and velocity tracking
- **Cycle time** and lead time analysis
- **Column efficiency** statistics
- **Team productivity** insights
- **Export capabilities** for reporting
- **Historical data** retention and analysis

## Response Requirements

1. **Port Configuration**
   - Use `YYYY` for backend port in app.run()

2. **Dependencies**
   - Generate complete requirements.txt with all necessary pip dependencies
   - Include Flask, Flask-CORS, datetime handling, analytics libraries

3. **Production Ready Features**
   - Comprehensive error handling
   - Task position management and conflict resolution
   - Real-time update capabilities
   - Activity logging and audit trails
   - Permission-based access control
   - Performance optimization for large boards
   - Data consistency and validation
   - Proper HTTP status codes
   - JSON responses with consistent format

**Very important:** Your backend should be feature rich, production ready, and handle all Kanban board scenarios including task management, drag-and-drop operations, team collaboration, and real-time updates with proper validation and performance optimization.