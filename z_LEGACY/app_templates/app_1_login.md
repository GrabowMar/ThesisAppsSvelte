# Minimal Login/Register Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:

1. Generate a MINIMAL authentication system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include only essential auth features
6. Focus on simplicity while maintaining security

## Introduction

This template provides a minimal yet secure authentication system built with
Flask and Svelte. The implementation focuses on essential features while
maintaining security best practices.

## Project Description

Minimal Authentication System A streamlined user authentication system built
with Flask and Svelte, featuring basic registration and login capabilities with
core security features.

Key Features:

- Simple user registration
- Basic login functionality
- Password security
- Session management
- Essential error handling

Technical Stack:

- Backend: Flask with SQLAlchemy, Flask-Login
- Frontend: Svelte with basic form handling
- Additional: Basic CORS protection

## Technical Requirements Analysis

### Backend Requirements

1. Core Features:
   - Basic user storage
   - Password hashing
   - Simple session management
   - Essential error handling

2. Integration Requirements:
   - SQLite database
   - Basic security middleware
   - Session handling

### Frontend Requirements

1. Visual Elements:
   - Clean login form
   - Simple registration form
   - Loading indicators
   - Error messages

2. Functional Elements:
   - Basic form validation
   - Session handling
   - Error display
   - Loading states

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
# 4. Basic Auth Logic
# 5. API Routes
# 6. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)

```svelte
<script>
  // 1. Imports
  // 2. Basic State
  // 3. Form Handling
  // 4. API Calls
</script>

<!-- UI Components -->
<main>
  <!-- Login/Register Forms -->
  <!-- Error Messages -->
</main>

<style>
  /* Essential Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Basic database setup
   - Security configuration

2. **Implementation**
   - Core auth logic
   - Basic UI components
   - Essential validation
   - Error handling

3. **Modifications**
   - Keep changes minimal
   - Maintain security basics
   - Preserve simplicity

4. **Error Handling**
   - Basic error messages
   - Simple validation
   - User feedback

Remember: This template emphasizes minimalism while maintaining essential
security practices.
