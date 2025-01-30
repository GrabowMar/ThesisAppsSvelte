# Minimal CRUD Inventory Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a MINIMAL inventory system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic CRUD operations
6. Focus on inventory management essentials

## Project Description

Minimal CRUD Inventory System
A basic inventory management system built with Flask and Svelte, featuring essential CRUD operations.

Key Features:
- Item management (CRUD)
- Basic inventory tracking
- Simple categorization
- Stock level alerts
- Search/filter items

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with form handling
- Additional: Data validation

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - CRUD operations
   - Stock tracking
   - Category management
   - Search functionality

2. Integration Requirements:
   - Database setup
   - Data validation
   - Query handling

### Frontend Requirements
1. Visual Elements:
   - Item list/grid
   - Edit form
   - Stock indicators
   - Category filters
   - Search interface

2. Functional Elements:
   - CRUD operations
   - Data filtering
   - Sort functionality
   - Stock alerts

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

Remember: This template emphasizes minimal CRUD functionality while maintaining the single-file architecture approach.