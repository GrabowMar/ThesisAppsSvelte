# Basic Reservation Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a BASIC reservation system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include essential booking features
6. Focus on time slot management

## Project Description

Basic Reservation System
A straightforward booking application built with Flask and Svelte, featuring time slot management and reservation handling.

Key Features:
- Time slot booking
- Availability check
- Reservation management
- Calendar view
- Booking confirmation

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with calendar
- Additional: Date/time handling

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Slot management
   - Booking processing
   - Availability checking
   - Calendar logic

2. Integration Requirements:
   - Database setup
   - Time handling
   - Booking validation

### Frontend Requirements
1. Visual Elements:
   - Calendar interface
   - Booking form
   - Time slot picker
   - Confirmation view
   - Availability display

2. Functional Elements:
   - Date selection
   - Time slot picking
   - Booking submission
   - Status updates

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

Remember: This template emphasizes basic reservation functionality while maintaining the single-file architecture approach.