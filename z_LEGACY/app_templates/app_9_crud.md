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
# 1. Imports Section

# 2. App Configuration

# 3. Database Models

# 4. CRUD Operations

# 5. Search/Filter Logic

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Item State

  // 3. CRUD Handlers

  // 4. Filter/Sort Logic

  // 5. Form Management
</script>

<!-- UI Components -->
<main>
  <!-- Item List/Grid -->
  <!-- CRUD Forms -->
  <!-- Filters/Search -->
  <!-- Alerts -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Database configuration
   - Item schema definition

2. **Implementation**
   - CRUD operations
   - Data management
   - Filter system
   - Alert handling

3. **Modifications**
   - Update operations
   - Adjust data model
   - Modify filters

4. **Error Handling**
   - Data validation
   - Operation status
   - User feedback

Remember: This template emphasizes minimal CRUD functionality while maintaining the single-file architecture approach.