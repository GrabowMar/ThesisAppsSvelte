```markdown
# Crypto Wallet Application Template - Flask + react

## Important Implementation Notes

1. Generate web app with properly implemented key features mentioned below.
2. Try to keep all changes within **app.py** , **App.jsx** and **App.css** files.
3. Try to write feature complete production ready app, with comments, fails states, etc.
4. **Note:** Multipage routing is possible within these files. On the backend, you can define multiple routes (e.g., `/login`, `/register`, `/dashboard`, etc.) in **app.py**. On the frontend, client-side routing can be managed within **App.jsx** using conditional rendering or a routing library, all within the single-file constraint.
5. Mounting Logic: The App.jsx file must include mounting logic. This means it should import ReactDOM from react-dom/client and use it to attach the main App component to the DOM element with the id "root".
## Project Description

**Crypto Wallet System**  
A cryptocurrency wallet built with Flask and react, featuring essential transaction capabilities.

**Required Features:**
- **Multipage Routing:** Extendable routing on both backend and frontend for additional pages/views
- SImple and modern UI

**Template Specific:**

- Balance checking
- Send/Receive functionality
- Transaction history
- Address management
- Basic security

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
│   │   ├── App.jsx      # ALL frontend logic (with potential multipage routing)
│   │   └── App.css         # (optional)
│   ├── Dockerfile          # (optional)
│   ├── package.json        # (generated if needed)
│   └── vite.config.js      # (required for port config)
│
└── docker-compose.yml      # (optional)
```

### Core Files Structure

#### Backend (app.py)
```python
# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# 4. Authentication Logic (if needed)
# 5. Utility Functions
# 6. API Routes
# 7. Error Handlers

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 'XXXX')))
```

#### Frontend (App.jsx)
```react
<script>
  // 1. Imports
  import { onMount } from 'react';

  // 2. State Management
  // 3. Lifecycle Functions
  // 4. Event Handlers
  // 5. API Calls
</script>

<!-- UI Components -->
<main>
  <!-- Component Structure -->
</main>
```

#### Vite (vite.config.js)
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: YYYY,
    strictPort: true
  }
})
```

## Response requirements

1. **Port Configuration Prompt**
   - Use `XXXX` (backend) and `YYYY` (frontend) ports.

2. **Backend Generation Prompt**
   - Must include all specified backend features.
   - Must list required pip dependencies in form of requirements.txt.


3. **Frontend Generation Prompt**
   - Must include all specified frontend features.
   - Must list required npm dependencies in form of package.json (and vite.config.js if necessary)


**Very important:** Your app should be feature rich and production ready.
```