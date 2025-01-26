# Tiny Fitness Logger Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a TINY fitness tracking system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic workout tracking
6. Focus on progress monitoring

## Project Description

Tiny Fitness Logger System
A minimal workout tracking application built with Flask and Svelte, featuring basic exercise and progress logging.

Key Features:
- Workout logging
- Progress tracking
- Basic statistics
- Exercise library
- Simple charts

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with charts
- Additional: Data visualization

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Workout management
   - Progress tracking
   - Stats calculation
   - Exercise handling

2. Integration Requirements:
   - Database setup
   - Data processing
   - Stats generation

### Frontend Requirements
1. Visual Elements:
   - Workout form
   - Progress charts
   - Exercise list
   - Stats display
   - Input controls

2. Functional Elements:
   - Workout logging
   - Progress viewing
   - Stats tracking
   - Chart updates

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

# 4. Workout Management

# 5. Stats Processing

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Workout State

  // 3. Progress Tracking

  // 4. Chart Management

  // 5. Stats Display
</script>

<!-- UI Components -->
<main>
  <!-- Workout Form -->
  <!-- Progress View -->
  <!-- Stats Display -->
  <!-- Charts -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Database setup
   - Exercise library

2. **Implementation**
   - Workout logging
   - Progress tracking
   - Stats calculation
   - Chart display

3. **Modifications**
   - Update workout types
   - Adjust tracking
   - Modify stats

4. **Error Handling**
   - Input validation
   - Data processing
   - User feedback

Remember: This template emphasizes tiny fitness tracking while maintaining the single-file architecture approach.