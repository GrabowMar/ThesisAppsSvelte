# Tiny E-Commerce Cart Application Template - Flask + Svelte

## Important Implementation Notes

As an AI assistant, when implementing this template:
1. Generate a TINY e-commerce cart system
2. Keep ALL changes within app.py and App.svelte files only
3. Do NOT modify the project structure
4. Do NOT create additional files unless explicitly requested
5. Include essential shopping features
6. Focus on cart management functionality

## Introduction

This template provides a tiny e-commerce cart system built with Flask and Svelte. The implementation focuses on essential shopping features while maintaining clean, maintainable code.

## Project Description

Tiny E-Commerce Cart System
A minimalist shopping cart application built with Flask and Svelte, featuring basic product management and cart functionality.

Key Features:
- Product listing
- Cart management
- Basic checkout
- Order summary
- Simple inventory

Technical Stack:
- Backend: Flask with SQLAlchemy
- Frontend: Svelte with state management
- Additional: Cart session handling

## Technical Requirements Analysis

### Backend Requirements
1. Core Features:
   - Product management
   - Cart operations
   - Order processing
   - Inventory tracking

2. Integration Requirements:
   - Database setup
   - Session handling
   - Cart persistence

### Frontend Requirements
1. Visual Elements:
   - Product grid
   - Cart display
   - Checkout form
   - Order summary
   - Inventory status

2. Functional Elements:
   - Cart operations
   - Product filtering
   - Quantity handling
   - Total calculation

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

# 4. Cart Management

# 5. Product Handling

# 6. Order Processing

# 7. API Routes

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.svelte)
```svelte
<script>
  // 1. Imports

  // 2. Cart State

  // 3. Product Handling

  // 4. Cart Operations

  // 5. Checkout Logic
</script>

<!-- UI Components -->
<main>
  <!-- Product List -->
  <!-- Cart View -->
  <!-- Checkout Form -->
  <!-- Order Summary -->
</main>

<style>
  /* Component Styles */
</style>
```

## Response Protocol

1. **Initial Setup**
   - Confirm ports (XXXX, YYYY)
   - Product data structure
   - Cart configuration

2. **Implementation**
   - Product management
   - Cart functionality
   - Checkout process
   - Order handling

3. **Modifications**
   - Update cart logic
   - Adjust product handling
   - Modify checkout flow

4. **Error Handling**
   - Inventory checks
   - Cart validation
   - User feedback

Remember: This template emphasizes essential e-commerce functionality while maintaining the single-file architecture approach.