# Simple Kanban Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a SIMPLE kanban system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic board features
6. Focus on task management essentials

## Project Description

Simple Kanban System
A basic task management application built with Flask and Svelte, featuring kanban board functionality.

Key Features:
- Board management
- Task creation/editing
- Column organization
- Drag-and-drop
- Basic filtering

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with drag-drop
- Additional: Task organization

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Board management
   - Task handling
   - Column operations
   - State tracking

2. Integration Requirements:
   - Database setup
   - Task storage
   - State persistence

### Frontend Requirements
1. Visual Elements:
   - Kanban board
   - Task cards
   - Column layout
   - Add/Edit forms
   - Filter controls

2. Functional Elements:
   - Drag-drop handling
   - Task management
   - Column ordering
   - Filter system

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
- Confirm ports (XXXX, YYYY)
- Generate backend remembering requested features
- Generate frontend remembering requested features


Remember: This template emphasizes simple kanban functionality while maintaining the single-file architecture approach.