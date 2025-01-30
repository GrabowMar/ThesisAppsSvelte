# Minimal Login/Register Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:

1. Generate a authentication system
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)

```svelte
<script>
</script>

<main>
</main>

<style>
</style>
```
## Response Protocol

### Protocol Steps

1. **Port Configuration Prompt**
   - Request port numbers for backend and frontend
   - Replace XXXX (backend) and YYYY (frontend) placeholders
   - Example format: "Please provide two port numbers for backend and frontend"

2. **Backend Generation Prompt**
   - Request complete app.py code generation
   - Must include all specified backend features
   - Must list required pip dependencies
   - Wait for user confirmation before proceeding
   - Try to aim for best practices and proffessionalism
   - Example format: "Generate the Flask frontend code with the specified features:"

3. **Frontend Generation Prompt**
   - Request complete App.svelte code generation
   - Must include all specified frontend features
   - Must list required npm dependencies
   - Try to aim for best practices and proffessionalism
   - Example format: "Generate the Svelte frontend code with the specified features:"

Note: Backend implementation must be confirmed before proceeding with frontend generation.
