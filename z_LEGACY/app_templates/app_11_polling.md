# Simple Polling Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a SIMPLE polling system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic voting features
6. Focus on poll management essentials

## Project Description

Simple Polling System
A basic voting application built with Flask and Svelte, featuring poll creation and voting functionality.

Key Features:
- Poll creation
- Vote casting
- Results display
- Basic analytics
- Time-limited polls

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with chart display
- Additional: Real-time updates

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Poll management
   - Vote processing 
   - Results calculation
   - Time tracking

2. Integration Requirements:
   - Database setup
   - Vote handling
   - Results caching

### Frontend Requirements
1. Visual Elements:
   - Poll creator
   - Voting interface
   - Results display
   - Charts view
   - Timer display

2. Functional Elements:
   - Vote submission
   - Results updates
   - Chart rendering
   - Timer handling

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

Remember: This template emphasizes simple polling functionality while maintaining the single-file architecture approach.