# Simple Map Sharing Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a SIMPLE map sharing system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic location features
6. Focus on map visualization

## Project Description

Simple Map Sharing System
A basic location sharing application built with Flask and Svelte, featuring map visualization.

Key Features:
- Map display
- Location sharing
- Basic markers
- Simple routes
- Location search

Technical Stack:
- Backend: Flask with geospatial
- Frontend: Svelte with map library
- Additional: Location services

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Location storage
   - Marker management
   - Route handling
   - Share system

2. Integration Requirements:
   - Database setup
   - Geo calculations
   - Share links

### Frontend Requirements
1. Visual Elements:
   - Map component
   - Location picker
   - Marker controls
   - Route display
   - Share interface

2. Functional Elements:
   - Map interaction
   - Location selection
   - Marker placement
   - Route drawing

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


Remember: This template emphasizes simple map sharing while maintaining the single-file architecture approach.