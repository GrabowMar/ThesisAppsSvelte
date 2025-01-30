# Minimal CRUD Inventory Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a MINIMAL microblog system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic CRUD operations
6. Focus on microblog essentials

## Project Description

Minimal CRUD Inventory System
A basic microblog system built with Flask and Svelte.


Key Features:
- Post creation and management (CRUD)
- User profile management
- Post timeline/feed
- Post interactions (likes/comments)
- Basic post search

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with state management
- Additional: User authentication

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Post CRUD operations
   - User authentication/profiles
   - Timeline/feed generation
   - Comment management
   - Like functionality

2. Integration Requirements:
   - User session management
   - Database relationships
   - Feed pagination
   - Search functionality

### Frontend Requirements
1. Visual Elements:
   - Post creation interface
   - Timeline/feed display
   - User profile page
   - Comment threads
   - Like/interaction buttons
   - Search bar

2. Functional Elements:
   - Real-time post updates
   - Comment threading
   - Profile customization
   - Feed sorting options
   - Post search/filtering


## Implementation Structure

### Project Layout
```plaintext
app/
├── backend/
│   ├── app.py              # ALL backend logic
│   ├── Dockerfile          # (optional)
│   └── requirements.txt    # (generated if needed)
│
├── frontend/
│   ├── src/
│   │   ├── App.svelte     # ALL frontend logic
│   │   └── main.js        # (optional)
│   ├── Dockerfile         # (optional)
│   ├── package.json       # (generated if needed)
│   └── vite.config.js     # (required for port config)
│
└── docker-compose.yml      # (optional)
```

### Core Files Structure

#### Backend (app.py)
```python

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
</script>

<main>
</main>

<style>
</style>
```

## Response Protocol

### Protocol Steps

1. **Port Configuration Prompt**
   - Request port numbers for backend and frontend
   - Replace XXXX (backend) and YYYY (frontend) placeholders
   - Example format: "Please provide two port numbers for backend and frontend"

2. **Backend Generation Prompt**
   - Request complete app.py code generation
   - Must include all specified backend features
   - Must list required pip dependencies
   - Wait for user confirmation before proceeding
   - Try to aim for best practices and proffessionalism
   - Example format: "Generate the Flask frontend code with the specified features:"

3. **Frontend Generation Prompt**
   - Request complete App.svelte code generation
   - Must include all specified frontend features
   - Must list required npm dependencies
   - Try to aim for best practices and proffessionalism
   - Example format: "Generate the Svelte frontend code with the specified features:"

Note: Backend implementation must be confirmed before proceeding with frontend generation.