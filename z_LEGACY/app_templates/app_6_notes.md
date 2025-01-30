# Basic Notes Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a BASIC note-taking system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include core note features
6. Focus on simple content management

## Project Description

Basic Notes System
A straightforward note-taking application built with Flask and Svelte, featuring essential content management capabilities.

Key Features:
- Note creation/editing
- Note listing/viewing
- Simple categorization
- Basic search
- Note archiving

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with state management
- Additional: Rich text support

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Note storage
   - Content management
   - Tag handling
   - Search functionality

2. Integration Requirements:
   - Database setup
   - Content processing
   - Query handling

### Frontend Requirements
1. Visual Elements:
   - Note editor
   - Note list
   - Search bar
   - Tag selector
   - Archive view

2. Functional Elements:
   - Content editing
   - Note filtering
   - Search handling
   - Tag management

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

Remember: This template emphasizes simple note management while maintaining the single-file architecture approach.