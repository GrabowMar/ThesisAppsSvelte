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
# 1. Imports Section

# 2. App Configuration

# 3. Database Models

# 4. Poll Management

# 5. Vote Processing

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Poll State

  // 3. Vote Handling

  // 4. Results Display

  // 5. Chart Management
</script>

<!-- UI Components -->
<main>
  <!-- Poll Creator -->
  <!-- Voting Interface -->
  <!-- Results View -->
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
   - Poll schema

2. **Implementation**
   - Poll creation
   - Vote handling
   - Results display
   - Charts/analytics

3. **Modifications**
   - Update poll logic
   - Adjust voting
   - Modify results

4. **Error Handling**
   - Vote validation
   - Poll status
   - User feedback

Remember: This template emphasizes simple polling functionality while maintaining the single-file architecture approach.