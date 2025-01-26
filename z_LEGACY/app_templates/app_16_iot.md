# Minimal IoT Controller Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a MINIMAL IoT control system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic device control features
6. Focus on essential monitoring and control

## Project Description

Minimal IoT Controller System
A basic IoT device management application built with Flask and Svelte, featuring device control and monitoring.

Key Features:
- Device management
- Status monitoring
- Basic controls
- Data display
- Simple automation

Technical Stack:
- Backend: Flask with WebSocket
- Frontend: Svelte with real-time updates
- Additional: Device communication

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Device connection
   - Status tracking
   - Command handling
   - Data processing

2. Integration Requirements:
   - WebSocket setup
   - Device protocol
   - Data storage

### Frontend Requirements
1. Visual Elements:
   - Device list
   - Control panel
   - Status display
   - Data charts
   - Command interface

2. Functional Elements:
   - Device control
   - Status updates
   - Data visualization
   - Command sending

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

# 3. WebSocket Setup

# 4. Device Management

# 5. Command Processing

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Device State

  // 3. WebSocket Handler

  // 4. Control Logic

  // 5. Data Display
</script>

<!-- UI Components -->
<main>
  <!-- Device List -->
  <!-- Control Panel -->
  <!-- Status Display -->
  <!-- Data View -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - WebSocket configuration
   - Device protocol

2. **Implementation**
   - Device management
   - Control interface
   - Status tracking
   - Data visualization

3. **Modifications**
   - Update device handling
   - Adjust controls
   - Modify displays

4. **Error Handling**
   - Connection issues
   - Command failures
   - User feedback

Remember: This template emphasizes minimal IoT control while maintaining the single-file architecture approach.