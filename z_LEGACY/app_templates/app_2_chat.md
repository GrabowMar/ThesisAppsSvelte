```markdown
# Chat Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a real-time chat system.
2. Keep ALL changes within **app.py** and **App.svelte** files only.
3. Do NOT modify the project structure.
4. Do NOT create additional files unless explicitly requested.
5. Include core messaging features.
6. Focus on real-time communication functionality.
7. **Note:** Multipage routing is supported in both backend and frontend. In **app.py**, you can define multiple routes for different API endpoints or pages, and in **App.svelte**, client-side routing can be implemented using conditional rendering or a routing library.

## Introduction

This template provides a chat system built with Flask and Svelte. The implementation focuses on real-time message exchange while maintaining clean, maintainable code.

## Project Description

**Chat System**  
A messaging application built with Flask and Svelte, featuring real-time communication capabilities and user interaction.

**Key Features:**

- Real-time message exchange
- User identification
- Message history
- Online status
- Chat rooms

**Technical Stack:**

- **Backend:** Flask with SocketIO
- **Frontend:** Svelte with WebSocket handling
- **Additional:** Event-driven updates

## Technical Requirements Analysis

### Backend Requirements
1. **Core Features:**
   - Message handling
   - WebSocket management
   - User tracking
   - Room management

2. **Integration Requirements:**
   - WebSocket setup
   - Message storage
   - User session handling

### Frontend Requirements
1. **Visual Elements:**
   - Message display area
   - Input field
   - User list
   - Room selection
   - Status indicators

2. **Functional Elements:**
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
│   │   ├── App.svelte      # ALL frontend logic (multipage routing supported)
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
  // Implement client-side routing here using conditional logic
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