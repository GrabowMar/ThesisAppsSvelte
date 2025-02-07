```markdown
# Login/Register Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:

1. Generate an authentication system.
2. Keep ALL changes within **app.py** and **App.svelte** files only.
3. Do NOT modify the project structure.
4. Do NOT create additional files unless explicitly requested.
5. Include only essential auth features.
6. Focus on security.
7. **Note:** Multipage routing is possible within these files. On the backend, you can define multiple routes (e.g., `/login`, `/register`, `/dashboard`, etc.) in **app.py**. On the frontend, client-side routing can be managed within **App.svelte** using conditional rendering or a routing library, all within the single-file constraint.

## Introduction

This template provides a secure authentication system built with Flask and Svelte. The implementation focuses on essential features while maintaining security best practices.

## Project Description

**Authentication System**  
A streamlined user authentication system built with Flask and Svelte, featuring user registration and login capabilities with core security features.

**Key Features:**

- User registration
- Login functionality
- Password security
- Session management
- Error handling
- **Multipage Routing:** Extendable routing on both backend and frontend for additional pages/views

**Technical Stack:**

- **Backend:** Flask with SQLAlchemy, Flask-Login
- **Frontend:** Svelte with form handling
- **Additional:** CORS protection

## Technical Requirements Analysis

### Backend Requirements

1. **Core Features:**
   - User storage
   - Password hashing
   - Session management
   - Error handling

2. **Integration Requirements:**
   - SQLite database
   - Security middleware
   - Session handling

### Frontend Requirements

1. **Visual Elements:**
   - Login form
   - Registration form
   - Loading indicators
   - Error messages

2. **Functional Elements:**
   - Form validation
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
│   │   ├── App.svelte      # ALL frontend logic (with potential multipage routing)
│   │   └── main.js         # (optional)
│   ├── Dockerfile          # (optional)
│   ├── package.json        # (generated if needed)
│   └── vite.config.js      # (required for port config)
│
└── docker-compose.yml      # (optional)
```

### Core Files Structure

#### Backend (app.py)

```python
# Example snippet in app.py showing port configuration and multipage routing possibilities

if __name__ == '__main__':
    # Replace 'XXXX' with the desired backend port.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)

```svelte
<script>
  // You can implement client-side routing here using conditional logic
  // or by integrating a routing library, all within this single file.
</script>

<main>
  <!-- Render different views based on routing logic -->
</main>

<style>
  /* Styles */
</style>
```

## Response Protocol

### Protocol Steps

1. **Port Configuration Prompt**
   - Request port numbers for backend and frontend.
   - Replace `XXXX` (backend) and `YYYY` (frontend) placeholders.
   - **Example format:** "Please provide two port numbers for backend and frontend."

2. **Backend Generation Prompt**
   - Request complete **app.py** code generation.
   - Must include all specified backend features.
   - Must list required pip dependencies.
   - Wait for user confirmation before proceeding.
   - Aim for best practices and professionalism.
   - **Example format:** "Generate the Flask backend code with the specified features:"

3. **Frontend Generation Prompt**
   - Request complete **App.svelte** code generation.
   - Must include all specified frontend features.
   - Must list required npm dependencies.
   - Aim for best practices and professionalism.
   - **Example format:** "Generate the Svelte frontend code with the specified features:"

**Note:** Backend implementation must be confirmed before proceeding with frontend generation.
```