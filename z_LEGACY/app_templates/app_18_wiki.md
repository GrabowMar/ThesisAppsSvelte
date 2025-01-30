# Basic Wiki Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a BASIC wiki system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include core wiki features
6. Focus on content management essentials

## Project Description

Basic Wiki System
A simple wiki platform built with Flask and Svelte, featuring page management and content organization.

Key Features:
- Page creation/editing
- Content organization
- Basic search
- Version history
- Simple formatting

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with markdown
- Additional: Content versioning

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Page management
   - Content versioning
   - Search functionality
   - Link handling

2. Integration Requirements:
   - Database setup
   - Content storage
   - Version control

### Frontend Requirements
1. Visual Elements:
   - Page editor
   - Content view
   - Search interface
   - History display
   - Navigation menu

2. Functional Elements:
   - Content editing
   - Page navigation
   - Search handling
   - Version control

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

Remember: This template emphasizes basic wiki functionality while maintaining the single-file architecture approach.