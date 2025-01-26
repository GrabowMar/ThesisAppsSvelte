# Mini Crypto Wallet Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a MINI cryptocurrency wallet system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include basic wallet features
6. Focus on transaction essentials

## Project Description

Mini Crypto Wallet System
A basic cryptocurrency wallet built with Flask and Svelte, featuring essential transaction capabilities.

Key Features:
- Balance checking
- Send/Receive
- Transaction history
- Address management
- Basic security

Technical Stack:
- Backend: Flask with crypto libraries
- Frontend: Svelte with encryption
- Additional: Blockchain integration

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Wallet management
   - Transaction handling
   - Balance tracking
   - Address handling

2. Integration Requirements:
   - Blockchain connection
   - Key management
   - Transaction signing

### Frontend Requirements
1. Visual Elements:
   - Balance display
   - Transaction form
   - Address book
   - History view
   - Security controls

2. Functional Elements:
   - Transaction creation
   - Address validation
   - Balance updates
   - History tracking

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

# 3. Wallet Management

# 4. Transaction Processing

# 5. Address Handling

# 6. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Wallet State

  // 3. Transaction Management

  // 4. Address Handling

  // 5. Security Functions
</script>

<!-- UI Components -->
<main>
  <!-- Balance Display -->
  <!-- Transaction Form -->
  <!-- Address Book -->
  <!-- History View -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Wallet configuration
   - Blockchain setup

2. **Implementation**
   - Wallet functions
   - Transaction handling
   - Address management
   - Security features

3. **Modifications**
   - Update transaction logic
   - Adjust security
   - Modify interfaces

4. **Error Handling**
   - Transaction validation
   - Network issues
   - User feedback

Remember: This template emphasizes mini wallet functionality while maintaining the single-file architecture approach.