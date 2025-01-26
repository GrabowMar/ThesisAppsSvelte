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
# 1. Imports Section

# 2. App Configuration

# 3. Database Models

# 4. Note Management

# 5. Tag Handling

# 6. Search Logic

# 7. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Note State

  // 3. Editor Setup

  // 4. Note Operations

  // 5. Search/Filter Logic
</script>

<!-- UI Components -->
<main>
  <!-- Note Editor -->
  <!-- Note List -->
  <!-- Search/Filters -->
  <!-- Tag Management -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Database configuration
   - Note structure definition

2. **Implementation**
   - Note management
   - Content editing
   - Search functionality
   - Tag system

3. **Modifications**
   - Update note handling
   - Adjust editor features
   - Modify search/filters

4. **Error Handling**
   - Content validation
   - Save operations
   - User feedback

Remember: This template emphasizes simple note management while maintaining the single-file architecture approach.