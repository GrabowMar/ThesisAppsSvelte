# Basic Chat Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a BASIC real-time chat system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include core messaging features
6. Focus on real-time communication functionality

## Introduction

This template provides a basic chat system built with Flask and Svelte. The implementation focuses on real-time message exchange while maintaining clean, maintainable code.

## Project Description

Basic Chat System
A straightforward messaging application built with Flask and Svelte, featuring real-time communication capabilities and basic user interaction.

Key Features:
- Real-time message exchange
- Basic user identification
- Message history
- Online status
- Simple chat rooms

Technical Stack:
- Backend: Flask with SocketIO
- Frontend: Svelte with WebSocket handling
- Additional: Event-driven updates

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Message handling
   - WebSocket management
   - Basic user tracking
   - Room management

2. Integration Requirements:
   - WebSocket setup
   - Message storage
   - User session handling

### Frontend Requirements
1. Visual Elements:
   - Message display area
   - Input field
   - User list
   - Room selection
   - Status indicators

2. Functional Elements:
   - Real-time updates
   - Message composition
   - Room switching
   - User status

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
   - Try to aim for best practices and professionalism
   - Example format: "Generate the Flask frontend code with the specified features:"

3. **Frontend Generation Prompt**
   - Request complete App.svelte code generation
   - Must include all specified frontend features
   - Must list required npm dependencies
   - Try to aim for best practices and professionalism
   - Example format: "Generate the Svelte frontend code with the specified features:"

Note: Backend implementation must be confirmed before proceeding with frontend generation.
