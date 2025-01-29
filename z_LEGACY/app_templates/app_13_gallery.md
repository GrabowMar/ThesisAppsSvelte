I'll help rewrite this for a gallery app instead of a reservation system. Here's the modified version:

# Basic Gallery Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a BASIC gallery system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include essential gallery features
6. Focus on image management

## Project Description

Basic Gallery System
A straightforward gallery application built with Flask and Svelte, featuring image management and gallery organization.

Key Features:
- Image upload
- Gallery organization
- Image viewing
- Grid/List views
- Image details/metadata

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with image handling
- Additional: Image processing

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Image storage
   - Gallery management
   - Metadata handling
   - Image processing

2. Integration Requirements:
   - Database setup
   - File handling
   - Image validation

### Frontend Requirements
1. Visual Elements:
   - Gallery interface
   - Upload form
   - Image grid/list
   - Image preview
   - Details display

2. Functional Elements:
   - Image selection
   - Upload handling
   - Gallery navigation
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

# 4. Image Management

# 5. Gallery Logic

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Gallery State

  // 3. Upload Handling

  // 4. Image Management

  // 5. Form Processing
</script>

<!-- UI Components -->
<main>
  <!-- Gallery View -->
  <!-- Upload Form -->
  <!-- Image Preview -->
  <!-- Details Display -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Database setup
   - Storage config

2. **Implementation**
   - Gallery setup
   - Upload flow
   - Image processing
   - Preview system

3. **Modifications**
   - Update galleries
   - Adjust layouts
   - Modify views

4. **Error Handling**
   - File validation
   - Storage limits
   - User feedback

Remember: This template emphasizes basic gallery functionality while maintaining the single-file architecture approach.
