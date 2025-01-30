# Compact Forum Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a COMPACT forum system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include essential discussion features
6. Focus on thread and comment management

## Project Description

Compact Forum System
A lightweight discussion platform built with Flask and Svelte, featuring thread and comment management.

Key Features:
- Thread creation/viewing
- Comment system
- Basic categories
- Simple sorting
- Thread search

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with state management
- Additional: Thread organization

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Thread management
   - Comment handling
   - Category system
   - Search functionality

2. Integration Requirements:
   - Database setup
   - Content storage
   - Query handling

### Frontend Requirements
1. Visual Elements:
   - Thread list
   - Thread view
   - Comment section
   - Category selector
   - Sort controls

2. Functional Elements:
   - Thread creation
   - Comment posting
   - Content sorting
   - Search handling

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

Remember: This template emphasizes compact discussion management while maintaining the single-file architecture appro