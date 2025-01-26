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
# 1. Imports Section

# 2. App Configuration

# 3. Database Models

# 4. Slot Management

# 5. Booking Logic

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Calendar State

  // 3. Booking Handling

  // 4. Time Management

  // 5. Form Processing
</script>

<!-- UI Components -->
<main>
  <!-- Calendar View -->
  <!-- Booking Form -->
  <!-- Time Picker -->
  <!-- Confirmations -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Database setup
   - Time zone config

2. **Implementation**
   - Calendar setup
   - Booking flow
   - Availability check
   - Confirmation system

3. **Modifications**
   - Update time slots
   - Adjust bookings
   - Modify calendar

4. **Error Handling**
   - Slot validation
   - Booking conflicts
   - User feedback

Remember: This template emphasizes basic reservation functionality while maintaining the single-file architecture approach.