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
# 1. Imports Section

# 2. App Configuration

# 3. Database Models

# 4. Thread Management

# 5. Comment Handling

# 6. Category System

# 7. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Thread State

  // 3. Comment Management

  // 4. Sort/Filter Logic

  // 5. Content Operations
</script>

<!-- UI Components -->
<main>
  <!-- Thread List -->
  <!-- Thread View -->
  <!-- Comment Section -->
  <!-- Category Nav -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Database setup
   - Thread structure

2. **Implementation**
   - Thread management
   - Comment system
   - Category handling
   - Search/sort

3. **Modifications**
   - Update thread logic
   - Adjust comments
   - Modify categories

4. **Error Handling**
   - Content validation
   - Post operations
   - User feedback

Remember: This template emphasizes compact discussion management while maintaining the single-file architecture appro