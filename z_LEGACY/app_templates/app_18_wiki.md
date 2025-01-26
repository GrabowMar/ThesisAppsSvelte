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
# 1. Imports Section

# 2. App Configuration

# 3. Database Models

# 4. Page Management

# 5. Version Control

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Page State

  // 3. Editor Setup

  // 4. Version Handling

  // 5. Search Logic
</script>

<!-- UI Components -->
<main>
  <!-- Page Editor -->
  <!-- Content View -->
  <!-- Search Bar -->
  <!-- History View -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Database setup
   - Content schema

2. **Implementation**
   - Page handling
   - Version control
   - Search system
   - Editor setup

3. **Modifications**
   - Update content management
   - Adjust versioning
   - Modify search

4. **Error Handling**
   - Content validation
   - Version conflicts
   - User feedback

Remember: This template emphasizes basic wiki functionality while maintaining the single-file architecture approach.