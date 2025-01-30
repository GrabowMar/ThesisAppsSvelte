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
- Confirm ports (XXXX, YYYY)
- Generate backend remembering requested features
- Generate frontend remembering requested features


Remember: This template emphasizes real-time communication while maintaining the single-file architecture approach.