# Mini File Uploader Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a MINI file upload system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic file handling features
6. Focus on upload/download functionality

## Project Description

Mini File Uploader System
A lightweight file handling application built with Flask and Svelte, featuring basic upload and download capabilities.

Key Features:
- File upload
- File listing
- Download functionality
- Basic file preview
- Simple organization

Technical Stack:
- Backend: Flask with file handling
- Frontend: Svelte with upload management
- Additional: Progress tracking

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - File processing
   - Storage management
   - Download handling
   - File organization

2. Integration Requirements:
   - File storage setup
   - Upload handling
   - Stream management

### Frontend Requirements
1. Visual Elements:
   - Upload zone
   - File list
   - Progress bars
   - Preview pane
   - Download buttons

2. Functional Elements:
   - Upload handling
   - Progress tracking
   - File selection
   - Download triggers

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

# 3. Storage Setup

# 4. Upload Handling

# 5. Download Management

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Upload State

  // 3. File Handling

  // 4. Progress Tracking

  // 5. Download Management
</script>

<!-- UI Components -->
<main>
  <!-- Upload Zone -->
  <!-- File List -->
  <!-- Progress Indicators -->
  <!-- Download Area -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Storage configuration
   - Upload limits

2. **Implementation**
   - Upload handling
   - File management
   - Download system
   - Progress tracking

3. **Modifications**
   - Update file handling
   - Adjust storage
   - Modify limits

4. **Error Handling**
   - Upload validation
   - Storage checks
   - User feedback

Remember: This template emphasizes simple file handling while maintaining the single-file architecture approach.