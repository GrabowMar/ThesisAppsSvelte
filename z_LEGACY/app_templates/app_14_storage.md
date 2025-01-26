# Mini Photo Gallery Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a MINI photo gallery system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include essential gallery features
6. Focus on image management basics

## Project Description

Mini Photo Gallery System
A lightweight image gallery built with Flask and Svelte, featuring basic photo management.

Key Features:
- Image upload
- Gallery view
- Basic categorization
- Simple slideshow
- Image preview

Technical Stack:
- Backend: Flask with image handling
- Frontend: Svelte with preview
- Additional: Image processing

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Image storage
   - File processing
   - Gallery management
   - Category handling

2. Integration Requirements:
   - File storage setup
   - Image processing
   - Thumbnail generation

### Frontend Requirements
1. Visual Elements:
   - Gallery grid
   - Image preview
   - Upload interface
   - Category filters
   - Slideshow view

2. Functional Elements:
   - Image upload
   - Gallery navigation
   - Preview handling
   - Category sorting

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

# 3. Image Processing

# 4. Gallery Management

# 5. File Handling

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

  // 4. Preview Logic

  // 5. Slideshow Management
</script>

<!-- UI Components -->
<main>
  <!-- Gallery Grid -->
  <!-- Upload Area -->
  <!-- Image Preview -->
  <!-- Slideshow -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Storage configuration
   - Image processing setup

2. **Implementation**
   - Upload handling
   - Gallery display
   - Preview system
   - Slideshow function

3. **Modifications**
   - Update gallery logic
   - Adjust processing
   - Modify preview

4. **Error Handling**
   - Upload validation
   - Processing errors
   - User feedback

Remember: This template emphasizes mini gallery functionality while maintaining the single-file architecture approach.